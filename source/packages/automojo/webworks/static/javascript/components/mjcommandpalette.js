/*
 * mjcommandpalette.js
 *
 * <mj-command-palette> -- keyboard-first, searchable command launcher. Modal
 * dialog with fuzzy-search input, grouped results, aria-activedescendant
 * navigation, and localStorage-persisted recent commands.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: contents;
}

.cp-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--mj-layer-modal);
  background: var(--mj-overlay-scrim);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 10vh;
  opacity: 0;
  transition: opacity var(--mj-motion-medium) var(--mj-motion-ease);
}

:host([open]) .cp-backdrop { opacity: 1; }
:host(:not([open])) .cp-backdrop { pointer-events: none; visibility: hidden; }

.cp-panel {
  width: min(var(--mj-cp-width, 38rem), calc(100vw - var(--mj-space-6)));
  max-height: var(--mj-cp-max-height, 60vh);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-cp-radius, var(--mj-radius-lg));
  box-shadow: var(--mj-cp-shadow, var(--mj-elevation-3));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform: translateY(-8px);
  transition: transform var(--mj-motion-medium) var(--mj-motion-ease);
}

:host([open]) .cp-panel { transform: translateY(0); }

.cp-input-row {
  display: flex;
  align-items: center;
  gap: var(--mj-space-3);
  padding: 0 var(--mj-space-4);
  height: var(--mj-cp-input-height, 3.5rem);
  border-bottom: 1px solid var(--mj-border);
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
  border-top: 1px solid var(--mj-border);
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  display: flex;
  gap: var(--mj-space-4);
}

.cp-footer:empty { display: none; }

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

@media (prefers-reduced-motion: reduce) {
  .cp-backdrop, .cp-panel { transition: none; }
}
`;

export class MjCommandPalette extends MjElement {
  static tagName = "mj-command-palette";
  static styles = STYLES;
  static watched = ["open", "placeholder", "empty-message", "max-results", "max-recent", "global-shortcut"];

  constructor() {
    super()
    this.commands = []
    this._results = []
    this._recentIds = []
    this._activeIndex = -1
    this._debounceTimer = null
    this._trapDispose = null
    this._overlay = null
    this._returnFocusEl = null
    this._inputEl = null
    this._listEl = null
    this._statusEl = null
    this._listId = nextId("mj-cp-list")
    this._onGlobalKeydown = this._handleGlobalShortcut.bind(this)
  }

  render() {
    const placeholder = this.getAttribute("placeholder") || "Type a command…"
    const dialogLabel = this.getAttribute("label") || "Command palette"
    const markup = `
      <div class="cp-backdrop" role="dialog" aria-modal="true" aria-label="${dialogLabel}" tabindex="-1">
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
              aria-activedescendant=""
              placeholder="${placeholder}"
              autocomplete="off"
              spellcheck="false" />
          </div>
          <ul class="cp-results" part="results" role="listbox" id="${this._listId}"></ul>
          <div class="cp-footer" part="footer">
            <slot name="footer">
              <span class="cp-hint"><kbd>&#x2191;</kbd><kbd>&#x2193;</kbd> Navigate</span>
              <span class="cp-hint"><kbd>&#x23CE;</kbd> Select</span>
              <span class="cp-hint"><kbd>Esc</kbd> Dismiss</span>
            </slot>
          </div>
        </div>
      </div>
      <div aria-live="polite" aria-atomic="true" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;"></div>
    `
    return markup
  }

  afterRender() {
    this._backdrop = this.$(".cp-backdrop")
    this._inputEl = this.$(".cp-input")
    this._listEl = this.$(".cp-results")
    this._statusEl = this.shadowRoot.querySelector("[aria-live]")

    this.listen(this._inputEl, "input", this._onInput.bind(this))
    this.listen(this._inputEl, "keydown", this._onInputKeydown.bind(this))
    this.listen(this._backdrop, "keydown", this._onBackdropKeydown.bind(this))
    this.listen(this._backdrop, "pointerdown", this._onBackdropPointerdown.bind(this))
    this.listen(this._listEl, "click", this._onListClick.bind(this))

    this._loadRecent()
    this._registerShortcut()

    if (this.hasAttribute("open") === true) {
      this._openPalette()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._inputEl !== null) {
      if (newValue !== null) {
        this._openPalette()
      } else {
        this._closePalette("api")
      }
    }
    if (name === "global-shortcut") {
      this._registerShortcut()
    }
    return
  }

  onDisconnected() {
    window.removeEventListener("keydown", this._onGlobalKeydown)
    this._cleanupTrap()
    this._hideOverlay()
    return
  }

  _registerShortcut() {
    window.removeEventListener("keydown", this._onGlobalKeydown)
    window.addEventListener("keydown", this._onGlobalKeydown)
    return
  }

  _handleGlobalShortcut(event) {
    const shortcutStr = this.getAttribute("global-shortcut") || "Meta+k,Ctrl+k"
    const combos = shortcutStr.split(",")

    for (let i = 0; i < combos.length; i = i + 1) {
      const parts = combos[i].trim().split("+")
      const key = parts[parts.length - 1].toLowerCase()
      const needsMeta = parts.includes("Meta")
      const needsCtrl = parts.includes("Ctrl")

      const keyMatch = event.key.toLowerCase() === key
      const metaMatch = needsMeta === false || event.metaKey === true
      const ctrlMatch = needsCtrl === false || event.ctrlKey === true
      const noConflict = needsMeta === true ? event.metaKey : event.ctrlKey

      if (keyMatch === true && (metaMatch === true || ctrlMatch === true) && noConflict === true) {
        event.preventDefault()
        if (this.hasAttribute("open") === false) {
          this.setAttribute("open", "")
        }
        return
      }
    }
    return
  }

  _openPalette() {
    this._returnFocusEl = document.activeElement
    this._showOverlay()
    this._trapDispose = trapFocus(this._backdrop, this._inputEl)
    this._inputEl.value = ""
    this._showRecent()
    this.emit("mj-command-palette-open", {})
    return
  }

  _closePalette(reason) {
    this._cleanupTrap()
    this._hideOverlay()
    this.removeAttribute("open")

    const restoreEl = this._returnFocusEl
    this._returnFocusEl = null
    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-command-palette-close", { reason: reason })
    return
  }

  _cleanupTrap() {
    if (this._trapDispose !== null) {
      this._trapDispose()
      this._trapDispose = null
    }
    return
  }

  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.setAttribute("visible", "")
    overlay.setAttribute("scroll-lock", "true")
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    this._overlay.remove()
    this._overlay = null
    return
  }

  _onInput() {
    const query = this._inputEl.value
    if (this._debounceTimer !== null) {
      window.clearTimeout(this._debounceTimer)
    }
    const delay = parseInt(this.getAttribute("debounce") || "120", 10)
    this._debounceTimer = window.setTimeout(() => {
      this._runFilter(query)
      this.emit("mj-command-palette-query", { query: query })
    }, delay)
    return
  }

  _runFilter(query) {
    const maxResults = parseInt(this.getAttribute("max-results") || "20", 10)

    if (query === null || query.trim().length === 0) {
      this._showRecent()
      return
    }

    const needle = query.toLowerCase()
    const scored = []

    for (let i = 0; i < this.commands.length; i = i + 1) {
      const cmd = this.commands[i]
      if (cmd.disabled === true) {
        continue
      }
      const label = (cmd.label || "").toLowerCase()
      const keywords = (cmd.keywords || []).join(" ").toLowerCase()
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
    this._results = scored.slice(0, maxResults).map((s) => s.cmd)
    this._renderResults(null, this._results)
    this._announceResults(this._results.length, query)
    this.emit("mj-command-palette-results", { results: this._results, query: query })
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

  _showRecent() {
    const maxRecent = parseInt(this.getAttribute("max-recent") || "5", 10)
    const recentCmds = []

    for (let i = 0; i < this._recentIds.length && recentCmds.length < maxRecent; i = i + 1) {
      const cmd = this.commands.find((c) => c.id === this._recentIds[i])
      if (cmd !== undefined) {
        recentCmds.push(cmd)
      }
    }

    if (recentCmds.length > 0) {
      this._renderResults("Recent", recentCmds)
    } else {
      this._renderResults(null, this.commands.slice(0, 10))
    }
    return
  }

  _renderResults(groupLabel, results) {
    if (this._listEl === null) {
      return
    }

    this._listEl.innerHTML = ""
    this._activeIndex = -1
    this._setActivedescendant("")

    if (results.length === 0) {
      const emptyMsg = this.getAttribute("empty-message") || "No matching commands"
      this._listEl.innerHTML = `
        <li class="cp-empty" part="empty" role="presentation">
          <slot name="empty"><span>${emptyMsg}</span></slot>
        </li>
      `
      return
    }

    if (groupLabel !== null) {
      const header = document.createElement("li")
      header.className = "cp-group-header"
      header.setAttribute("role", "presentation")
      header.setAttribute("part", "group-header")
      header.textContent = groupLabel
      this._listEl.appendChild(header)
    }

    for (let index = 0; index < results.length; index = index + 1) {
      const cmd = results[index]
      const itemId = `${this._listId}-item-${index}`
      const li = document.createElement("li")
      li.id = itemId
      li.className = "cp-item"
      li.setAttribute("role", "option")
      li.setAttribute("aria-selected", "false")
      li.setAttribute("part", "item")
      li.setAttribute("data-cmd-index", String(index))
      if (cmd.disabled === true) {
        li.setAttribute("aria-disabled", "true")
      }

      const shortcutHtml = cmd.shortcut
        ? `<span class="cp-item-shortcut" part="item-shortcut"><kbd>${cmd.shortcut}</kbd></span>`
        : ""

      li.innerHTML = `
        <span class="cp-item-icon" part="item-icon" aria-hidden="true">${cmd.icon || ""}</span>
        <span class="cp-item-label" part="item-label" title="${cmd.label || ""}">${cmd.label || ""}</span>
        ${shortcutHtml}
      `

      this._listEl.appendChild(li)
    }

    this._setActiveItem(0)
    return
  }

  _setActiveItem(index) {
    const items = Array.from(this._listEl.querySelectorAll(".cp-item[role='option']:not([aria-disabled='true'])"))
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
      this._inputEl.setAttribute("aria-activedescendant", id)
    }
    return
  }

  _announceResults(count, query) {
    if (this._statusEl === null) {
      return
    }
    if (count === 0) {
      const emptyMsg = this.getAttribute("empty-message") || "No matching commands"
      this._statusEl.textContent = emptyMsg
    } else {
      this._statusEl.textContent = `${count} command${count === 1 ? "" : "s"} found`
    }
    return
  }

  _onInputKeydown(event) {
    const items = Array.from(this._listEl.querySelectorAll(".cp-item[role='option']:not([aria-disabled='true'])"))
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
        const idx = parseInt(items[this._activeIndex].getAttribute("data-cmd-index") || "0", 10)
        this._selectResult(idx)
      }
      return
    }
    return
  }

  _onBackdropKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      this._closePalette("escape")
    }
    return
  }

  _onBackdropPointerdown(event) {
    if (event.target === this._backdrop) {
      this._closePalette("backdrop")
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
    const idx = parseInt(item.getAttribute("data-cmd-index") || "0", 10)
    this._selectResult(idx)
    return
  }

  _selectResult(resultIndex) {
    const cmd = this._results[resultIndex]
    if (cmd === undefined) {
      return
    }

    const proceed = this.emit("mj-command-palette-select", { command: cmd }, { cancelable: true })
    if (proceed === false) {
      return
    }

    if (typeof cmd.action === "function") {
      cmd.action()
    } else if (cmd.href !== undefined) {
      window.location.href = cmd.href
    }

    this._recordRecent(cmd.id)
    this._closePalette("select")
    return
  }

  _recordRecent(id) {
    const maxRecent = parseInt(this.getAttribute("max-recent") || "5", 10)
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

  _loadRecent() {
    const key = this._storageKey()
    try {
      const raw = localStorage.getItem(key)
      if (raw !== null) {
        this._recentIds = JSON.parse(raw)
      }
    } catch (err) {
      this._recentIds = []
    }
    return
  }

  _storageKey() {
    return "mj-command-palette-recent"
  }

  /* Scriptable API */

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
