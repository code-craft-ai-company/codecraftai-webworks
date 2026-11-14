/*
 * mjsharebutton.js
 *
 * <mj-share-button> -- invokes the platform Web Share API to share a URL,
 * title, and optional text. Falls back to an inline share menu containing
 * at minimum a "Copy link" action and optional consumer-configured targets
 * when the Web Share API is unavailable or when force-menu is set.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import { escapeHtml, safeUrl } from "../core/html.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
  position: relative;
}

.btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-share-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-share-button-color, var(--mj-text));
  background: var(--mj-share-button-bg, var(--mj-surface));
  border: 1px solid var(--mj-share-button-border-color, var(--mj-border-strong));
  border-radius: var(--mj-share-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}
.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-share-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}
.btn[aria-expanded="true"] { background: var(--mj-bg-muted); }

/* Variants */
:host([variant="primary"]) .btn  { color: var(--mj-text-on-accent); background: var(--mj-accent); border-color: var(--mj-accent); }
:host([variant="primary"]) .btn:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }
:host([variant="tertiary"]) .btn { background: transparent; border-color: transparent; }
:host([variant="tertiary"]) .btn:hover { background: var(--mj-bg-muted); }

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

/* Icon-only: the label stays in the accessibility tree but is not shown. */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }
:host([icon-only]) .label {
  position: absolute;
  width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

/* Built-in share icon, used when the icon slot is left empty. */
.icon { display: inline-flex; }
.default-icon { width: 1em; height: 1em; }
:host([disabled]) .btn  { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .btn   { opacity: 0.55; cursor: progress; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-share-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-share-spin { to { transform: rotate(360deg); } }

/* Fallback menu */
.fallback-menu {
  position: absolute;
  inset-block-start: calc(100% + var(--mj-space-1));
  inset-inline-start: 0;
  min-width: var(--mj-share-button-menu-width, 12rem);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  z-index: var(--mj-layer-popover);
  list-style: none;
  margin: 0;
  padding: var(--mj-space-1) 0;
}
.fallback-menu[hidden] { display: none; }

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  width: 100%;
  padding: var(--mj-space-2) var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: none;
  border: none;
  cursor: pointer;
  text-align: start;
}
.menu-item:hover { background: var(--mj-bg-muted); }
.menu-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -2px;
}

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
}
`;

const SHARE_ICON_SVG = `<svg class="default-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="12" cy="3.5" r="1.75"/><circle cx="4" cy="8" r="1.75"/><circle cx="12" cy="12.5" r="1.75"/><line x1="5.6" y1="7.1" x2="10.4" y2="4.4"/><line x1="5.6" y1="8.9" x2="10.4" y2="11.6"/></svg>`;

export class MjShareButton extends MjElement {
  static tagName = "mj-share-button";
  static styles = STYLES;
  static watched = ["share-url", "share-title", "share-text", "force-menu", "variant", "size", "disabled", "loading", "icon-only", "label", "menu-label"];

  constructor() {
    super()
    this._button = null
    this._menu = null
    this._menuSlot = null
    this._menuOpen = false
    this._shareTargets = []
    this._shareData = null
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon" part="icon" aria-hidden="true"><slot name="icon">${SHARE_ICON_SVG}</slot></span>
        <span class="label" part="label"><slot></slot></span>
      </button>
      <ul class="fallback-menu" part="fallback-menu" role="menu" hidden>
        <li role="presentation">
          <button class="menu-item copy-link-item" part="menu-item" role="menuitem" type="button" tabindex="-1">${escapeHtml(t("mj.shareButton.copyLink"))}</button>
        </li>
        <li role="presentation">
          <button class="menu-item email-item" part="menu-item" role="menuitem" type="button" tabindex="-1">${escapeHtml(t("mj.shareButton.email"))}</button>
        </li>
        <slot name="menu-item"></slot>
      </ul>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this._menu = this.$(".fallback-menu")
    this._menuSlot = this.$("slot[name='menu-item']")

    /* The shadow DOM was just rebuilt with a closed menu. */
    this._menuOpen = false

    this.listen(this._button, "click", this._onClick.bind(this))
    this.listen(this._button, "keydown", this._onButtonKeydown.bind(this))
    this.listen(this.$(".copy-link-item"), "click", this._onCopyLink.bind(this))
    this.listen(this.$(".email-item"), "click", this._onEmail.bind(this))
    this.listen(this._menu, "click", this._onTargetClick.bind(this))
    this.listen(this._menu, "keydown", this._onMenuKeydown.bind(this))

    /* Escape and focus loss are handled only while focus is in the component. */
    this.listen(this, "keydown", this._onKeydown.bind(this))
    this.listen(this, "focusout", this._onFocusOut.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._renderTargets()
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button === undefined || this._button === null) {
      return
    }
    this._syncAccessibility()
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true
    const iconOnly = this.hasAttribute("icon-only")
    const label = this.getAttribute("label") || t("mj.shareButton.share")
    const menuLabel = this.getAttribute("menu-label") || t("mj.shareButton.shareVia")

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", loading === true ? "true" : "false")

    if (this.canShare === false) {
      this._button.setAttribute("aria-haspopup", "menu")
      this._button.setAttribute("aria-expanded", this._menuOpen === true ? "true" : "false")
    } else {
      this._button.removeAttribute("aria-haspopup")
      this._button.removeAttribute("aria-expanded")
    }

    /*
     * The name is the visible slotted label; an icon-only button, or one
     * without slotted text, takes it from `label` (default "Share").
     */
    const slottedText = this.textContent !== null ? this.textContent.trim() : ""
    if (iconOnly === true || slottedText === "" || this.hasAttribute("label") === true) {
      this._button.setAttribute("aria-label", label)
    } else {
      this._button.removeAttribute("aria-label")
    }

    if (this._menu !== null) {
      this._menu.setAttribute("aria-label", menuLabel)
    }
    return
  }

  _buildShareData() {
    if (this._shareData !== null && this._shareData !== undefined) {
      return this._shareData
    }
    const shareUrl = this.getAttribute("share-url") || window.location.href
    const shareTitle = this.getAttribute("share-title") || document.title
    const shareText = this.getAttribute("share-text") || undefined
    const data = { url: shareUrl, title: shareTitle }
    if (shareText !== undefined) {
      data.text = shareText
    }
    return data
  }

  /*
   * Build one menu entry per configured share target, ahead of the slotted
   * entries. Labels are set as text; nothing from a target is parsed as
   * markup.
   */
  _renderTargets() {
    if (this._menu === undefined || this._menu === null) {
      return
    }

    const stale = this._menu.querySelectorAll("li.target-entry")
    for (let index = 0; index < stale.length; index = index + 1) {
      stale[index].remove()
    }

    for (let index = 0; index < this._shareTargets.length; index = index + 1) {
      const target = this._shareTargets[index]
      if (target === null || typeof target !== "object") {
        continue
      }

      const entry = document.createElement("li")
      entry.className = "target-entry"
      entry.setAttribute("role", "presentation")

      const item = document.createElement("button")
      item.className = "menu-item target-item"
      item.type = "button"
      item.tabIndex = -1
      item.setAttribute("part", "menu-item")
      item.setAttribute("role", "menuitem")
      item.setAttribute("data-target-index", String(index))
      item.textContent = target.label !== undefined && target.label !== null ? String(target.label) : ""

      entry.appendChild(item)
      this._menu.insertBefore(entry, this._menuSlot)
    }
    return
  }

  /* The focusable menu entries in visual order: built-in, configured, slotted. */
  _getMenuItems() {
    const items = Array.from(this._menu.querySelectorAll(".menu-item"))
    if (this._menuSlot !== null) {
      const slotted = this._menuSlot.assignedElements({ flatten: true })
      for (let index = 0; index < slotted.length; index = index + 1) {
        items.push(slotted[index])
      }
    }
    return items
  }

  _focusMenuItem(index) {
    const items = this._getMenuItems()
    if (items.length === 0) {
      return
    }
    const wrapped = ((index % items.length) + items.length) % items.length
    items[wrapped].focus()
    return
  }

  /* Index of the menu entry that holds focus, or -1. */
  _focusedMenuItemIndex() {
    const items = this._getMenuItems()
    const shadowActive = this.shadowRoot.activeElement
    const lightActive = this.getRootNode().activeElement

    let focusedIndex = -1
    for (let index = 0; index < items.length; index = index + 1) {
      const item = items[index]
      if (item === shadowActive || item === lightActive || item.contains(lightActive) === true) {
        focusedIndex = index
        break
      }
    }
    return focusedIndex
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    if (this.canShare === true) {
      this._invokeNativeShare()
    } else {
      this._toggleMenu()
    }
    return
  }

  /* Arrow Down / Arrow Up on the trigger open the menu on its first / last entry. */
  _onButtonKeydown(event) {
    const isArrow = event.key === "ArrowDown" || event.key === "ArrowUp"
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (isArrow === false || blocked === true || this.canShare === true) {
      return
    }

    event.preventDefault()
    if (this._menuOpen === false) {
      this._openMenu()
    }
    if (event.key === "ArrowUp") {
      this._focusMenuItem(-1)
    } else {
      this._focusMenuItem(0)
    }
    return
  }

  /* Roving focus inside the open menu. */
  _onMenuKeydown(event) {
    const current = this._focusedMenuItemIndex()
    let handled = true

    if (event.key === "ArrowDown") {
      this._focusMenuItem(current + 1)
    } else if (event.key === "ArrowUp") {
      this._focusMenuItem(current - 1)
    } else if (event.key === "Home") {
      this._focusMenuItem(0)
    } else if (event.key === "End") {
      this._focusMenuItem(-1)
    } else if (event.key === "Tab") {
      /* Tab leaves the menu; the menu does not stay open behind the focus. */
      handled = false
      this._closeMenu()
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
      event.stopPropagation()
    }
    return
  }

  _invokeNativeShare() {
    const data = this._buildShareData()
    this.loading = true

    navigator.share(data).then(() => {
      this.loading = false
      this.emit("mj-share", { method: "native", data: data })
    }).catch((err) => {
      this.loading = false
      if (err.name === "AbortError") {
        return
      }
      this.emit("mj-share-error", { error: err })
    })
    return
  }

  _toggleMenu() {
    if (this._menuOpen === true) {
      this._closeMenu()
    } else {
      this._openMenu()
      this._focusMenuItem(0)
    }
    return
  }

  _openMenu() {
    this._menuOpen = true
    this._menu.hidden = false
    this._button.setAttribute("aria-expanded", "true")
    this.emit("mj-menu-open", {})
    return
  }

  _closeMenu() {
    if (this._menuOpen === false) {
      return
    }
    this._menuOpen = false
    this._menu.hidden = true
    this._button.setAttribute("aria-expanded", "false")
    this.emit("mj-menu-close", {})
    return
  }

  /* Close the menu after an entry was chosen and return focus to the trigger. */
  _closeMenuAfterChoice() {
    this._closeMenu()
    if (this._button !== null) {
      this._button.focus()
    }
    return
  }

  _onCopyLink() {
    const data = this._buildShareData()
    const shareUrl = data.url !== undefined && data.url !== null ? String(data.url) : window.location.href

    const clipboardAvailable =
      navigator.clipboard !== undefined &&
      navigator.clipboard !== null &&
      typeof navigator.clipboard.writeText === "function"

    if (clipboardAvailable === true) {
      navigator.clipboard.writeText(shareUrl).then(() => {
        this._onCopyLinkDone(data)
      }).catch((err) => {
        this._copyLinkWithFallback(shareUrl, data, err)
      })
    } else {
      this._copyLinkWithFallback(shareUrl, data, new Error("Clipboard API unavailable"))
    }
    return
  }

  _onCopyLinkDone(data) {
    this._closeMenuAfterChoice()
    this.emit("mj-share-select", { target: "copy-link", data: data })
    announce(t("mj.shareButton.linkCopied"), "polite")
    return
  }

  /*
   * Copy through a temporary textarea and execCommand("copy"); report the
   * failure with mj-share-error when that does not work either.
   */
  _copyLinkWithFallback(shareUrl, data, originalError) {
    let copied = false

    const helper = document.createElement("textarea")
    helper.value = shareUrl
    helper.setAttribute("readonly", "")
    helper.setAttribute("aria-hidden", "true")
    helper.tabIndex = -1
    helper.style.position = "fixed"
    helper.style.insetBlockStart = "0"
    helper.style.insetInlineStart = "0"
    helper.style.opacity = "0"

    document.body.appendChild(helper)
    try {
      helper.select()
      copied = document.execCommand("copy") === true
    } catch (error) {
      copied = false
    }
    helper.remove()

    if (copied === true) {
      this._onCopyLinkDone(data)
    } else {
      this._closeMenuAfterChoice()
      this.emit("mj-share-error", { error: originalError, target: "copy-link" })
      announce(t("mj.shareButton.copyFailed"), "assertive")
    }
    return
  }

  _onEmail() {
    const data = this._buildShareData()
    const subject = encodeURIComponent(data.title || "")
    const body = encodeURIComponent(data.url || "")
    window.open(`mailto:?subject=${subject}&body=${body}`, "_self")
    this._closeMenuAfterChoice()
    this.emit("mj-share-select", { target: "email", data: data })
    return
  }

  /* Activation of an entry built from `shareTargets`. */
  _onTargetClick(event) {
    const path = event.composedPath()

    let item = null
    for (let index = 0; index < path.length; index = index + 1) {
      const node = path[index]
      if (node === this._menu) {
        break
      }
      if (node.classList !== undefined && node.classList.contains("target-item") === true) {
        item = node
        break
      }
    }
    if (item === null) {
      return
    }

    const targetIndex = parseInt(item.getAttribute("data-target-index"), 10)
    const target = this._shareTargets[targetIndex]
    if (target === undefined || target === null) {
      return
    }

    const data = this._buildShareData()
    this._closeMenuAfterChoice()

    if (typeof target.handler === "function") {
      target.handler(data, target)
    } else if (target.href !== undefined && target.href !== null) {
      const href = safeUrl(target.href, "")
      if (href !== "") {
        window.open(href, "_blank", "noopener")
      }
    }

    this.emit("mj-share-select", { target: target.label, item: target, data: data })
    return
  }

  /*
   * Escape closes the menu only when the key was pressed inside the
   * component, so it never pulls focus away from another control.
   */
  _onKeydown(event) {
    if (event.key === "Escape" && this._menuOpen === true) {
      event.stopPropagation()
      this._closeMenu()
      this._button.focus()
    }
    return
  }

  /* Close the menu when focus moves to an element outside the component. */
  _onFocusOut(event) {
    const next = event.relatedTarget
    if (next === null || next === undefined) {
      return
    }

    const stillInside = next === this || this.contains(next) === true
    if (stillInside === false && this._menuOpen === true) {
      this._closeMenu()
    }
    return
  }

  _onDocClick(event) {
    if (this._menuOpen === true && this.contains(event.target) === false) {
      this._closeMenu()
    }
    return
  }

  /* ----- scriptable API ----- */

  /*
   * True when the platform share sheet will be used: the Web Share API
   * exists, accepts the current share data, and `force-menu` is not set.
   */
  get canShare() {
    const forceMenu = this.hasAttribute("force-menu")
    if (forceMenu === true) {
      return false
    }

    let available = typeof navigator.share === "function"
    if (available === true && typeof navigator.canShare === "function") {
      try {
        available = navigator.canShare(this._buildShareData()) === true
      } catch (error) {
        available = false
      }
    }
    return available
  }

  get shareData() {
    return this._shareData
  }

  set shareData(value) {
    this._shareData = value
    if (this._button !== undefined && this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  get shareTargets() {
    return this._shareTargets
  }

  set shareTargets(value) {
    this._shareTargets = Array.isArray(value) === true ? value : []
    this._renderTargets()
    return
  }

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", Boolean(value))
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /*
   * Shares as a user click would (the share sheet, or the fallback menu).
   * HTMLElement.click() would only dispatch a click at the host, which never
   * reaches the inner button. Disabled / busy states are honoured by the
   * inner handler.
   */
  click() {
    if (this._button !== undefined && this._button !== null) {
      this._button.click()
    }
    return
  }

  focus(options) {
    if (this._button !== undefined && this._button !== null) {
      this._button.focus(options)
    }
    return
  }
}
