/*
 * mjcommandpalette.js
 *
 * <mj-command-palette> -- keyboard-first, searchable command launcher. Modal
 * surface with a fuzzy-search input, grouped results, aria-activedescendant
 * navigation, an optional asynchronous result source and localStorage-
 * persisted recent commands.
 *
 * Commands are supplied through the `commands` property:
 *   { id, label, icon?, shortcut?, group?, keywords?, action?, href?, disabled? }
 * `label`, `shortcut` and `group` are text. `icon` is text too (HTML
 * character references such as "&#x1F4C4;" are decoded, markup is not
 * interpreted), or a DOM node the caller built, which is cloned. `href` is
 * followed only when it is a safe URL.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html, safeUrl } from "../core/html.js";
import { t } from "../core/intl.js";
import { trapFocus, deepActiveElement } from "../core/focustrap.js";
import { pushLayer, removeLayer, claimEscape, hasModalLayer } from "../core/overlay.js";

const DEFAULT_SHORTCUT = "Meta+k,Ctrl+k";
const DEFAULT_STORAGE_KEY = "mj-command-palette-recent";

const STYLES = `
:host {
  display: contents;
}

.cp-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--mj-layer-modal);
  box-sizing: border-box;
  margin: 0;
  border: 0 none;
  width: 100%;
  height: 100%;
  background: var(--mj-overlay-scrim);
  color: var(--mj-text);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 10vh 0 0;
  outline: none;
  opacity: 0;
  transition: opacity var(--mj-motion-medium) var(--mj-motion-ease);
}

:host([open]) .cp-backdrop { opacity: 1; }
:host(:not([open])) .cp-backdrop { pointer-events: none; visibility: hidden; }

.cp-panel {
  width: min(var(--mj-cp-width, 38rem), calc(100vw - var(--mj-space-6)));
  max-height: var(--mj-cp-max-height, 60vh);
  background: var(--mj-cp-bg, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-cp-radius, var(--mj-radius-lg));
  box-shadow: var(--mj-cp-shadow, var(--mj-elevation-3));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:host([open]) .cp-panel {
  animation: mj-cp-in var(--mj-motion-medium) var(--mj-motion-ease);
}

@keyframes mj-cp-in {
  from { transform: translateY(-8px); }
  to   { transform: none; }
}

.cp-input-row {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  padding: 0 var(--mj-space-4);
  height: var(--mj-cp-input-height, 3.5rem);
  border-block-end: 1px solid var(--mj-border);
  flex-shrink: 0;
}

.cp-input-prefix { color: var(--mj-text-muted); flex-shrink: 0; }

.cp-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  caret-color: var(--mj-accent);
}

.cp-input::placeholder { color: var(--mj-text-muted); }

.cp-results {
  flex: 1;
  overflow-y: auto;
  list-style: none;
  margin: 0;
  padding: var(--mj-space-1) 0;
  min-height: 4rem;
}

.cp-group-header {
  padding: var(--mj-space-2) var(--mj-space-4) var(--mj-space-1);
  font-size: var(--mj-font-size-xs);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.cp-item {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  padding: 0 var(--mj-space-4);
  height: var(--mj-cp-item-height, 2.5rem);
  cursor: pointer;
  color: var(--mj-text);
  font-size: var(--mj-font-size-sm);
}

.cp-item[aria-selected="true"] {
  background: var(--mj-cp-highlight-bg, var(--mj-bg-muted));
}

.cp-item[aria-disabled="true"] { opacity: 0.4; pointer-events: none; }

.cp-item-icon { flex-shrink: 0; width: 1.25rem; text-align: center; }
.cp-item-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cp-item-shortcut { color: var(--mj-text-muted); font-size: var(--mj-font-size-xs); }

.cp-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--mj-space-6) var(--mj-space-4);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.cp-footer {
  flex-shrink: 0;
  padding: var(--mj-space-2) var(--mj-space-4);
  border-block-start: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  display: flex;
  gap: var(--mj-space-4);
}

.cp-hint { display: flex; align-items: center; gap: var(--mj-space-1); }
.cp-hint kbd {
  display: inline-flex;
  align-items: center;
  padding: 0 0.3rem;
  background: var(--mj-bg-muted);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  font: inherit;
  font-size: var(--mj-font-size-xs);
}

.cp-status {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
  .cp-backdrop { transition: none; }
  :host([open]) .cp-panel { animation: none; }
}
`;

/*
 * Turn an icon string into plain text: HTML character references are
 * decoded and any markup is dropped, never interpreted. The template is
 * inert -- nothing in it loads or runs.
 */
function iconText(value) {
  const template = document.createElement("template")
  template.innerHTML = String(value)
  const text = template.content.textContent || ""
  return text
}

/* True for an element the user types text into. */
function isEditable(element) {
  let editable = false
  if (element instanceof HTMLInputElement) {
    const nonText = ["button", "checkbox", "radio", "range", "color", "file", "submit", "reset", "image"]
    editable = nonText.indexOf(element.type) < 0
  } else if (element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement) {
    editable = true
  } else if (element instanceof HTMLElement && element.isContentEditable === true) {
    editable = true
  }
  return editable
}

/*
 * Parse a shortcut list such as "Meta+k, Ctrl+Shift+P, /" into
 * { key, meta, ctrl, alt, shift } records. An empty string yields none.
 */
function parseShortcuts(text) {
  const combos = []
  const entries = text.split(",")

  for (let index = 0; index < entries.length; index = index + 1) {
    const entry = entries[index].trim()
    if (entry.length === 0) {
      continue
    }

    /* "Ctrl++" means Ctrl and the plus key. */
    const parts = entry.endsWith("++") === true
      ? [...entry.slice(0, -2).split("+"), "+"]
      : entry.split("+")
    const key = parts[parts.length - 1].trim()
    const modifiers = parts.slice(0, -1).map((part) => part.trim().toLowerCase())

    if (key.length === 0) {
      continue
    }

    combos.push({
      key: key.toLowerCase(),
      meta: modifiers.includes("meta") === true || modifiers.includes("cmd") === true,
      ctrl: modifiers.includes("ctrl") === true || modifiers.includes("control") === true,
      alt: modifiers.includes("alt") === true || modifiers.includes("option") === true,
      shift: modifiers.includes("shift") === true
    })
  }

  return combos
}

export class MjCommandPalette extends MjElement {
  static tagName = "mj-command-palette";
  static styles = STYLES;
  static watched = [
    "open", "placeholder", "empty-message", "max-results", "max-recent", "global-shortcut",
    "label", "storage-key", "recent-label"
  ];

  constructor() {
    super()
    this._commands = []
    this._results = []
    this._recentIds = []
    this._activeIndex = -1
    this._debounceTimer = null
    this._trapDispose = null
    this._layer = null
    this._overlay = null
    this._returnFocusEl = null
    this._backdrop = null
    this._inputEl = null
    this._listEl = null
    this._statusEl = null
    this._listId = nextId("mj-cp-list")
    this._onGlobalKeydown = this._handleGlobalShortcut.bind(this)

    /* True from a successful open until the close has completed. */
    this._isOpen = false

    /* Increments per query, so a late asynchronous answer is discarded. */
    this._queryToken = 0

    /* Optional async source: (query) => Promise<CommandDescriptor[]>. */
    this.filterFn = null
  }

  render() {
    const markup = html`
      <div class="cp-backdrop" part="backdrop" role="dialog" aria-modal="true" tabindex="-1">
        <div class="cp-panel" part="dialog">
          <div class="cp-input-row" part="input-wrapper">
            <span class="cp-input-prefix" part="input-prefix" aria-hidden="true">
              <slot name="input-prefix">&#x1F50D;</slot>
            </span>
            <input class="cp-input" part="input" type="text"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="${this._listId}"
              aria-expanded="true"
              autocomplete="off"
              spellcheck="false" />
          </div>
          <ul class="cp-results" part="results" role="listbox" id="${this._listId}"></ul>
          <div class="cp-footer" part="footer">
            <slot name="footer">
              <span class="cp-hint"><kbd>&#x2191;</kbd><kbd>&#x2193;</kbd> ${t("mj.commandPalette.hintNavigate")}</span>
              <span class="cp-hint"><kbd>&#x23CE;</kbd> ${t("mj.commandPalette.hintSelect")}</span>
              <span class="cp-hint"><kbd>Esc</kbd> ${t("mj.commandPalette.hintDismiss")}</span>
            </slot>
          </div>
        </div>
        <div class="cp-status" aria-live="polite" aria-atomic="true"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".cp-backdrop")
    this._inputEl = this.$(".cp-input")
    this._listEl = this.$(".cp-results")
    this._statusEl = this.$(".cp-status")

    this.listen(this._inputEl, "input", this._onInput.bind(this))
    this.listen(this._inputEl, "keydown", this._onInputKeydown.bind(this))
    this.listen(this._backdrop, "keydown", this._onBackdropKeydown.bind(this))
    this.listen(this._backdrop, "pointerdown", this._onBackdropPointerdown.bind(this))
    this.listen(this._listEl, "click", this._onListClick.bind(this))
    this.listen(this._listEl, "pointermove", this._onListPointerMove.bind(this))
    this.listen(this._listEl, "mousedown", (event) => {
      /* Clicking a result must not take focus away from the input. */
      event.preventDefault()
    })

    window.addEventListener("keydown", this._onGlobalKeydown)
    this.onTeardown(() => {
      window.removeEventListener("keydown", this._onGlobalKeydown)
    })

    this._applyTexts()
    this._loadRecent()

    if (this.hasAttribute("open") === true) {
      this._openPalette()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._inputEl === undefined || this._inputEl === null) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._openPalette()
      } else if (this._isOpen === true) {
        this._closePalette("api")
      }
    } else if (name === "placeholder" || name === "label") {
      this._applyTexts()
    } else if (name === "storage-key") {
      this._loadRecent()
      if (this._isOpen === true) {
        this._refresh()
      }
    } else if (name === "empty-message" || name === "max-results" || name === "max-recent" || name === "recent-label") {
      if (this._isOpen === true) {
        this._refresh()
      }
    }
    return
  }

  onDisconnected() {
    /* Removed while open: release everything without events or refocus. */
    if (this._isOpen === true) {
      this._leaveOpenState()
      this._isOpen = false
    }
    if (this._debounceTimer !== null) {
      window.clearTimeout(this._debounceTimer)
      this._debounceTimer = null
    }
    return
  }

  _applyTexts() {
    this._inputEl.setAttribute("placeholder", this.getAttribute("placeholder") || t("mj.commandPalette.placeholder"))
    this._backdrop.setAttribute("aria-label", this.getAttribute("label") || t("mj.commandPalette.label"))
    return
  }

  _intAttribute(name, fallback) {
    const parsed = parseInt(this.getAttribute(name) || "", 10)
    const value = Number.isFinite(parsed) === true && parsed >= 0 ? parsed : fallback
    return value
  }

  /* ----- global shortcut ----- */

  /*
   * The combos in `global-shortcut` open the palette. Every modifier is
   * matched exactly ("Ctrl+Shift+P" needs Shift, "Ctrl+P" must not have it),
   * an empty attribute disables the shortcut, and nothing happens while
   * another modal surface is open (the palette would open beneath it).
   */
  _handleGlobalShortcut(event) {
    if (this._isOpen === true || event.defaultPrevented === true || event.repeat === true) {
      return
    }

    const attribute = this.getAttribute("global-shortcut")
    const combos = parseShortcuts(attribute !== null ? attribute : DEFAULT_SHORTCUT)
    if (combos.length === 0) {
      return
    }

    const path = event.composedPath()
    const origin = path.length > 0 ? path[0] : event.target
    const pressed = event.key.toLowerCase()

    for (let index = 0; index < combos.length; index = index + 1) {
      const combo = combos[index]

      /*
       * A symbol such as "?" or "/" may need Shift on some keyboards to be
       * typed at all, so Shift is only compared for letters, digits and
       * named keys -- or when the combo names it.
       */
      const isSymbol = /^[^a-z0-9]$/.test(combo.key) === true
      const shiftOk = combo.shift === event.shiftKey || (combo.shift === false && isSymbol === true)
      const matches = pressed === combo.key &&
        combo.meta === event.metaKey &&
        combo.ctrl === event.ctrlKey &&
        combo.alt === event.altKey &&
        shiftOk === true
      if (matches === false) {
        continue
      }

      /*
       * Typing in a field wins over a shortcut that has no Ctrl/Meta/Alt
       * ("/" types a slash), and rich-text editors keep their own Ctrl+K.
       */
      const plainKey = combo.meta === false && combo.ctrl === false && combo.alt === false
      const typing = isEditable(origin) === true
      const richText = origin instanceof HTMLElement && origin.isContentEditable === true
      if ((plainKey === true && typing === true) || richText === true) {
        return
      }

      if (hasModalLayer() === true) {
        return
      }

      event.preventDefault()
      this.setAttribute("open", "")
      return
    }
    return
  }

  /* ----- open / close ----- */

  _openPalette() {
    if (this._backdrop === null || this._isOpen === true || this.isConnected === false) {
      return
    }

    this._isOpen = true
    this._returnFocusEl = deepActiveElement()

    this._showOverlay()
    this._layer = pushLayer({
      surface: this._backdrop,
      modal: true,
      onEscape: () => {
        this._closePalette("escape")
      }
    })
    this._trapDispose = trapFocus(this._backdrop, this._inputEl, { contain: true })

    this._inputEl.value = ""
    this._runFilter("")
    this.emit("mj-command-palette-open", {})
    return
  }

  _leaveOpenState() {
    this._queryToken = this._queryToken + 1

    if (this._layer !== null) {
      removeLayer(this._layer)
      this._layer = null
    }
    if (this._trapDispose !== null) {
      /* Focus is restored by the caller, once nothing is inert any more. */
      this._trapDispose({ restoreFocus: false })
      this._trapDispose = null
    }
    this._hideOverlay()
    return
  }

  /* Close once; every route (Escape, backdrop, selection, API) comes here. */
  _closePalette(reason) {
    if (this._isOpen === false) {
      return
    }

    this._isOpen = false
    this._leaveOpenState()

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }

    const restoreEl = this._returnFocusEl
    this._returnFocusEl = null
    if (restoreEl !== null && restoreEl.isConnected === true && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-command-palette-close", { reason: reason })
    return
  }

  /*
   * The palette paints its own scrim, so <mj-overlay> is transparent: it
   * makes the page inert, locks scrolling and puts the palette in the top
   * layer.
   */
  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.surface = this._backdrop
    overlay.setAttribute("variant", "transparent")
    overlay.setAttribute("top-layer", "")
    overlay.setAttribute("visible", "")
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  /*
   * retire() releases inert and the scroll lock at once (so focus can be
   * restored right after) and removes the element when its fade has ended.
   */
  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    const overlay = this._overlay
    this._overlay = null
    if (typeof overlay.retire === "function") {
      overlay.retire()
    } else {
      overlay.remove()
    }
    return
  }

  /* ----- filtering ----- */

  _onInput() {
    const query = this._inputEl.value
    if (this._debounceTimer !== null) {
      window.clearTimeout(this._debounceTimer)
    }
    const delay = this._intAttribute("debounce", 120)
    this._debounceTimer = window.setTimeout(() => {
      this._debounceTimer = null
      this._runFilter(query)
      this.emit("mj-command-palette-query", { query: query })
    }, delay)
    return
  }

  /* Re-run the current query (after commands or settings changed). */
  _refresh() {
    this._runFilter(this._inputEl.value)
    return
  }

  _runFilter(query) {
    this._queryToken = this._queryToken + 1
    const token = this._queryToken
    const text = query !== null && query !== undefined ? query : ""

    if (text.trim().length === 0) {
      this._showRecent()
      return
    }

    if (typeof this.filterFn === "function") {
      this._runAsyncFilter(text, token)
      return
    }

    const results = this._localMatches(text)
    this._renderResults(null, results)
    this._announceResults(this._results.length)
    this.emit("mj-command-palette-results", { results: this._results.slice(), query: text })
    return
  }

  _localMatches(query) {
    const maxResults = this._intAttribute("max-results", 20)
    const needle = query.toLowerCase()
    const scored = []

    for (let i = 0; i < this._commands.length; i = i + 1) {
      const cmd = this._commands[i]
      if (cmd === null || typeof cmd !== "object" || cmd.disabled === true) {
        continue
      }
      const label = String(cmd.label || "").toLowerCase()
      const keywords = Array.isArray(cmd.keywords) ? cmd.keywords.join(" ").toLowerCase() : ""
      const haystack = label + " " + keywords

      let score = 0
      if (label.startsWith(needle) === true) {
        score = 3
      } else if (haystack.includes(needle) === true) {
        score = 2
      } else if (this._fuzzyMatch(haystack, needle) === true) {
        score = 1
      }

      if (score > 0) {
        const recentBonus = this._recentIds.indexOf(cmd.id) >= 0 ? 0.5 : 0
        scored.push({ cmd: cmd, score: score + recentBonus })
      }
    }

    scored.sort((a, b) => b.score - a.score)
    const matches = scored.slice(0, maxResults).map((entry) => entry.cmd)
    return matches
  }

  /* Results from `filterFn`; an answer for an outdated query is dropped. */
  _runAsyncFilter(query, token) {
    this._listEl.setAttribute("aria-busy", "true")
    this._renderMessage(t("core.loading"))

    let pending = null
    try {
      pending = Promise.resolve(this.filterFn(query))
    } catch (error) {
      pending = Promise.reject(error)
    }

    pending.then((value) => {
      if (token !== this._queryToken || this._isOpen === false) {
        return
      }
      this._listEl.removeAttribute("aria-busy")
      const maxResults = this._intAttribute("max-results", 20)
      const list = Array.isArray(value) ? value.filter((cmd) => cmd !== null && typeof cmd === "object") : []
      this._renderResults(null, list.slice(0, maxResults))
      this._announceResults(this._results.length)
      this.emit("mj-command-palette-results", { results: this._results.slice(), query: query })
    }, (error) => {
      if (token !== this._queryToken) {
        return
      }
      console.error("<mj-command-palette>: filterFn failed", error)
      this._listEl.removeAttribute("aria-busy")
      this._renderResults(null, [])
      this._announceResults(0)
    })
    return
  }

  _fuzzyMatch(text, pattern) {
    let ti = 0
    let pi = 0
    while (ti < text.length && pi < pattern.length) {
      if (text[ti] === pattern[pi]) {
        pi = pi + 1
      }
      ti = ti + 1
    }
    return pi === pattern.length
  }

  /* Empty query: recent commands, or the first commands when there are none. */
  _showRecent() {
    const maxRecent = this._intAttribute("max-recent", 5)
    const recentCmds = []

    for (let i = 0; i < this._recentIds.length && recentCmds.length < maxRecent; i = i + 1) {
      const cmd = this._commands.find((c) => c !== null && typeof c === "object" && c.id === this._recentIds[i])
      if (cmd !== undefined && cmd.disabled !== true) {
        recentCmds.push(cmd)
      }
    }

    if (recentCmds.length > 0) {
      this._renderResults(this.getAttribute("recent-label") || t("mj.commandPalette.recent"), recentCmds)
    } else {
      const firstCommands = this._commands.filter((c) => c !== null && typeof c === "object").slice(0, 10)
      this._renderResults(null, firstCommands)
    }
    return
  }

  /* ----- rendering ----- */

  _renderMessage(text) {
    this._listEl.textContent = ""
    const li = document.createElement("li")
    li.className = "cp-empty"
    li.setAttribute("part", "empty")
    li.setAttribute("role", "presentation")
    const span = document.createElement("span")
    span.textContent = text
    li.appendChild(span)
    this._listEl.appendChild(li)
    return
  }

  /*
   * Render `results` and make them the list that selection resolves
   * against. With `groupLabel` every result sits under that one heading;
   * otherwise results are grouped by their `group` field, groups in order
   * of first appearance.
   */
  _renderResults(groupLabel, results) {
    if (this._listEl === null) {
      return
    }

    const groups = []
    if (groupLabel !== null) {
      groups.push({ label: groupLabel, items: results.slice() })
    } else {
      const byName = new Map()
      for (const cmd of results) {
        const name = cmd.group !== undefined && cmd.group !== null ? String(cmd.group) : ""
        if (byName.has(name) === false) {
          const group = { label: name.length > 0 ? name : null, items: [] }
          byName.set(name, group)
          groups.push(group)
        }
        byName.get(name).items.push(cmd)
      }
    }

    /* `_results` follows the displayed order, so a row's index is its command. */
    this._results = []
    for (const group of groups) {
      for (const cmd of group.items) {
        this._results.push(cmd)
      }
    }

    this._listEl.textContent = ""
    this._activeIndex = -1
    this._setActivedescendant("")

    if (this._results.length === 0) {
      const li = document.createElement("li")
      li.className = "cp-empty"
      li.setAttribute("part", "empty")
      li.setAttribute("role", "presentation")
      const slot = document.createElement("slot")
      slot.setAttribute("name", "empty")
      const span = document.createElement("span")
      span.textContent = this.getAttribute("empty-message") || t("mj.commandPalette.empty")
      slot.appendChild(span)
      li.appendChild(slot)
      this._listEl.appendChild(li)
      return
    }

    let rowIndex = 0
    for (const group of groups) {
      if (group.label !== null) {
        const header = document.createElement("li")
        header.className = "cp-group-header"
        header.setAttribute("role", "presentation")
        header.setAttribute("part", "group-header")
        header.textContent = group.label
        this._listEl.appendChild(header)
      }

      for (const cmd of group.items) {
        this._listEl.appendChild(this._buildRow(cmd, rowIndex))
        rowIndex = rowIndex + 1
      }
    }

    this._setActiveItem(0)
    return
  }

  _buildRow(cmd, rowIndex) {
    const li = document.createElement("li")
    li.id = `${this._listId}-item-${rowIndex}`
    li.className = "cp-item"
    li.setAttribute("role", "option")
    li.setAttribute("aria-selected", "false")
    li.setAttribute("part", "item")
    li.setAttribute("data-cmd-index", String(rowIndex))
    if (cmd.disabled === true) {
      li.setAttribute("aria-disabled", "true")
    }

    const icon = document.createElement("span")
    icon.className = "cp-item-icon"
    icon.setAttribute("part", "item-icon")
    icon.setAttribute("aria-hidden", "true")
    if (cmd.icon instanceof Node) {
      icon.appendChild(cmd.icon.cloneNode(true))
    } else if (cmd.icon !== undefined && cmd.icon !== null) {
      icon.textContent = iconText(cmd.icon)
    }
    li.appendChild(icon)

    const labelText = cmd.label !== undefined && cmd.label !== null ? String(cmd.label) : ""
    const label = document.createElement("span")
    label.className = "cp-item-label"
    label.setAttribute("part", "item-label")
    label.setAttribute("title", labelText)
    label.textContent = labelText
    li.appendChild(label)

    if (cmd.shortcut !== undefined && cmd.shortcut !== null && String(cmd.shortcut).length > 0) {
      const shortcut = document.createElement("span")
      shortcut.className = "cp-item-shortcut"
      shortcut.setAttribute("part", "item-shortcut")
      const kbd = document.createElement("kbd")
      kbd.textContent = String(cmd.shortcut)
      shortcut.appendChild(kbd)
      li.appendChild(shortcut)
    }

    return li
  }

  _enabledRows() {
    const rows = Array.from(this._listEl.querySelectorAll(".cp-item[role='option']:not([aria-disabled='true'])"))
    return rows
  }

  _setActiveItem(index) {
    const items = this._enabledRows()
    if (items.length === 0) {
      return
    }

    const clamped = Math.max(0, Math.min(index, items.length - 1))

    for (let i = 0; i < items.length; i = i + 1) {
      items[i].setAttribute("aria-selected", i === clamped ? "true" : "false")
    }

    this._activeIndex = clamped
    this._setActivedescendant(items[clamped].id)

    items[clamped].scrollIntoView({ block: "nearest" })
    return
  }

  _setActivedescendant(id) {
    if (this._inputEl !== null) {
      if (id.length > 0) {
        this._inputEl.setAttribute("aria-activedescendant", id)
      } else {
        this._inputEl.removeAttribute("aria-activedescendant")
      }
    }
    return
  }

  _announceResults(count) {
    if (this._statusEl === null) {
      return
    }
    if (count === 0) {
      this._statusEl.textContent = this.getAttribute("empty-message") || t("mj.commandPalette.empty")
    } else {
      this._statusEl.textContent = t("mj.commandPalette.resultCount", { count: count })
    }
    return
  }

  /* ----- events ----- */

  _onInputKeydown(event) {
    const items = this._enabledRows()
    const count = items.length

    if (event.key === "ArrowDown") {
      event.preventDefault()
      this._setActiveItem(this._activeIndex + 1 < count ? this._activeIndex + 1 : 0)
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      this._setActiveItem(this._activeIndex - 1 >= 0 ? this._activeIndex - 1 : count - 1)
      return
    }

    if (event.key === "PageDown") {
      event.preventDefault()
      this._setActiveItem(Math.min(this._activeIndex + 5, count - 1))
      return
    }

    if (event.key === "PageUp") {
      event.preventDefault()
      this._setActiveItem(Math.max(this._activeIndex - 5, 0))
      return
    }

    if (event.key === "Enter") {
      event.preventDefault()
      if (this._activeIndex >= 0 && this._activeIndex < items.length) {
        const idx = parseInt(items[this._activeIndex].getAttribute("data-cmd-index") || "-1", 10)
        this._selectResult(idx)
      }
      return
    }
    return
  }

  _onBackdropKeydown(event) {
    if (event.key === "Escape") {
      const mine = claimEscape(event, this._layer)
      event.preventDefault()
      if (mine === true) {
        this._closePalette("escape")
      }
    }
    return
  }

  _onBackdropPointerdown(event) {
    if (event.target === this._backdrop) {
      this._closePalette("backdrop")
    }
    return
  }

  /* The row under the pointer becomes the active row. */
  _onListPointerMove(event) {
    const row = event.target.closest(".cp-item")
    if (row === null) {
      return
    }
    const rows = this._enabledRows()
    const position = rows.indexOf(row)
    if (position >= 0 && position !== this._activeIndex) {
      this._setActiveItem(position)
    }
    return
  }

  _onListClick(event) {
    const item = event.target.closest(".cp-item")
    if (item === null) {
      return
    }
    if (item.getAttribute("aria-disabled") === "true") {
      return
    }
    const idx = parseInt(item.getAttribute("data-cmd-index") || "-1", 10)
    this._selectResult(idx)
    return
  }

  _selectResult(resultIndex) {
    const cmd = this._results[resultIndex]
    if (cmd === undefined || cmd.disabled === true) {
      return
    }

    const proceed = this.emit("mj-command-palette-select", { command: cmd }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this._recordRecent(cmd.id)
    this._closePalette("select")

    if (typeof cmd.action === "function") {
      cmd.action(cmd)
    } else if (cmd.href !== undefined && cmd.href !== null) {
      const href = safeUrl(cmd.href, "")
      if (href.length > 0 && href !== "#") {
        window.location.assign(href)
      } else {
        console.warn("<mj-command-palette>: refusing to navigate to an unsafe href")
      }
    }
    return
  }

  /* ----- recent commands ----- */

  _recordRecent(id) {
    if (id === undefined || id === null) {
      return
    }
    const maxRecent = this._intAttribute("max-recent", 5)
    this._recentIds = this._recentIds.filter((rid) => rid !== id)
    this._recentIds.unshift(id)
    if (this._recentIds.length > maxRecent) {
      this._recentIds = this._recentIds.slice(0, maxRecent)
    }
    this._saveRecent()
    return
  }

  _saveRecent() {
    const key = this._storageKey()
    try {
      localStorage.setItem(key, JSON.stringify(this._recentIds))
    } catch (err) {
      /* localStorage unavailable; in-memory only */
    }
    return
  }

  /* Only an array of ids is accepted from storage; anything else is ignored. */
  _loadRecent() {
    const key = this._storageKey()
    let ids = []
    try {
      const stored = localStorage.getItem(key)
      if (stored !== null) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) === true) {
          ids = parsed.filter((entry) => typeof entry === "string" || typeof entry === "number")
        }
      }
    } catch (err) {
      ids = []
    }
    this._recentIds = ids
    return
  }

  /* Palettes with different command sets keep separate recents via `storage-key`. */
  _storageKey() {
    const key = this.getAttribute("storage-key")
    const storageKey = key !== null && key.length > 0 ? key : DEFAULT_STORAGE_KEY
    return storageKey
  }

  /* Scriptable API */

  /*
   * The available commands. An accessor (not a plain field) so that a value
   * assigned before the element was upgraded is picked up, and so that an
   * open palette shows the new commands at once.
   */
  get commands() {
    return this._commands
  }

  set commands(value) {
    this._commands = Array.isArray(value) ? value : []
    if (this._isOpen === true) {
      this._refresh()
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
    return
  }

  get query() {
    return this._inputEl !== null ? this._inputEl.value : ""
  }

  get results() {
    return this._results.slice()
  }

  /* The highlighted result, or null. */
  get activeItem() {
    let item = null
    if (this._listEl !== null && this._activeIndex >= 0) {
      const rows = this._enabledRows()
      const row = rows[this._activeIndex]
      if (row !== undefined) {
        const cmd = this._results[parseInt(row.getAttribute("data-cmd-index") || "-1", 10)]
        item = cmd !== undefined ? cmd : null
      }
    }
    return item
  }

  get recentIds() {
    return this._recentIds.slice()
  }

  show() {
    this.setAttribute("open", "")
    return
  }

  close() {
    this._closePalette("api")
    return
  }
}
