/*
 * mjcombobox.js
 *
 * <mj-combobox> — filterable/searchable input with popup suggestion list.
 * Supports sync options, an async data source, free-text mode, and clearable.
 *
 * Suggestions come from one of three places:
 *   - the <mj-option> descendants of the host, filtered as the user types. A
 *     MutationObserver follows them, so a consumer may replace the options
 *     in response to `mj-filter` (the documented async pattern);
 *   - the `dataSource` property: an object whose `query(text)` returns (a
 *     promise of) an array of { value, label, disabled } items, or
 *     { items: [...] };
 *   - the `src` attribute: a URL fetched with `?q=<text>` appended, returning
 *     the same JSON shape.
 *
 * The `value` attribute is the default value (what a form reset restores);
 * the live value is the `value` property. The text in the input and the
 * committed value are reconciled whenever focus leaves the control.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { autoPosition } from "../core/overlay.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: inline-block; vertical-align: middle; }
:host([block]) { display: block; }

.wrapper {
  display: flex;
  align-items: center;
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-combobox-border-radius, var(--mj-radius-md));
  background: var(--mj-surface);
  min-height: var(--mj-combobox-input-height, var(--mj-control-height-md));
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
}
.wrapper:focus-within { border-color: var(--mj-accent); }
:host([invalid]) .wrapper { border-color: var(--mj-color-danger); }
:host(:state(user-invalid)) .wrapper { border-color: var(--mj-color-danger); }
.wrapper.is-disabled { opacity: 0.55; pointer-events: none; }

.prefix { padding: 0 var(--mj-space-2); color: var(--mj-text-muted); display: flex; align-items: center; }
.prefix[hidden] { display: none; }
.input {
  flex: 1;
  min-width: 0;
  padding: 0 var(--mj-space-3);
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  height: 100%;
  min-height: var(--mj-combobox-input-height, var(--mj-control-height-md));
}
:host([size="sm"]) .wrapper,
:host([size="sm"]) .input { min-height: var(--mj-combobox-input-height, var(--mj-control-height-sm)); }
:host([size="sm"]) .input,
:host([size="sm"]) .option { font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .wrapper,
:host([size="lg"]) .input { min-height: var(--mj-combobox-input-height, var(--mj-control-height-lg)); }
:host([size="lg"]) .input,
:host([size="lg"]) .option { font-size: var(--mj-font-size-lg); }

.clear, .toggle {
  flex-shrink: 0;
  padding: 0 var(--mj-space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  display: flex;
  align-items: center;
}
.clear:hover, .toggle:hover { color: var(--mj-text); }
.clear:focus-visible, .toggle:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
:host(:not([clearable])) .clear { display: none; }
.clear.hidden { display: none; }

.popup {
  position: fixed;
  background: var(--mj-surface-raised, var(--mj-surface));
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-combobox-border-radius, var(--mj-radius-md));
  box-shadow: var(--mj-elevation-2);
  max-height: var(--mj-combobox-popup-max-height, 18rem);
  overflow-y: auto;
  /* At least as wide as the field (--_anchor-width, set on open) unless the page says otherwise. */
  min-inline-size: var(--mj-combobox-popup-min-width, var(--_anchor-width, 0px));
  z-index: var(--mj-layer-popover);
  display: none;
}
:host([open]) .popup { display: block; }

.listbox { padding: var(--mj-space-1) 0; }

.option {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  color: var(--mj-text);
  font-size: var(--mj-font-size-md);
}
.option:hover, .option.focused { background: var(--mj-bg-muted); }
.option[aria-selected="true"] { background: var(--mj-bg-subtle); }
.option[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }

.no-results, .loading, .error-inline {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  text-align: center;
  font-size: var(--mj-font-size-sm);
}
.error-inline { color: var(--mj-color-danger); }

mark {
  background: transparent;
  color: var(--mj-combobox-match-color, var(--mj-accent));
  font-weight: var(--mj-font-weight-medium);
}
`;

/* Option attributes whose changes alter what the suggestion list shows. */
const OPTION_ATTRIBUTES = ["value", "disabled", "label"]

const DEFAULT_DEBOUNCE_MS = 300
const DEFAULT_MIN_CHARS = 1

/*
 * Text content of `node` with the subtree of `skip` left out, whitespace
 * collapsed. Used to read a wrapping <label> without the combobox's own
 * option text.
 */
function textExcluding(node, skip) {
  const parts = []
  const visit = (current) => {
    if (current === skip) {
      return
    }
    if (current.nodeType === Node.TEXT_NODE) {
      parts.push(current.textContent)
      return
    }
    const children = current.childNodes
    for (let index = 0; index < children.length; index = index + 1) {
      visit(children[index])
    }
  }
  visit(node)
  const rtnval = parts.join(" ").replace(/\s+/g, " ").trim()
  return rtnval
}

/* Parse a non-negative integer attribute, falling back when it is absent or malformed. */
function readCount(element, name, fallback) {
  let count = fallback
  const text = element.getAttribute(name)
  if (text !== null) {
    const parsed = parseInt(text, 10)
    if (Number.isNaN(parsed) === false && parsed >= 0) {
      count = parsed
    }
  }
  return count
}

export class MjCombobox extends FormControlMixin(MjElement) {
  static tagName = "mj-combobox";
  static styles = STYLES;
  static watched = [
    "value", "open", "disabled", "readonly", "required", "invalid", "placeholder",
    "clearable", "free-text", "size", "src", "label", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* The text shown in the input; differs from the value while editing. */
    this._inputValue = ""

    /* True once the user has typed since the last commit or revert. */
    this._editing = false

    /* The label that belongs to the committed value, kept for async options. */
    this._valueLabel = null

    this._focusedIndex = -1
    this._optionData = []
    this._visibleItems = []
    this._debounceTimer = null
    this._disposePosition = null

    /* Async suggestions. */
    this._dataSource = null
    this._filterFn = null
    this._remoteOptions = null
    this._loadState = "idle"   /* "idle" | "loading" | "error" */
    this._loadToken = 0
    this._abortController = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* The `value` attribute change applied before the first render, if any. */
    this._preRenderValue = null

    this._listboxId = nextId("mj-cb-lb")
    this._inputId = nextId("mj-cb-in")
  }

  render() {
    const markup = `
      <div class="wrapper" part="wrapper">
        <span class="prefix" part="prefix" aria-hidden="true"><slot name="prefix"></slot></span>
        <input
          class="input"
          part="input"
          id="${this._inputId}"
          role="combobox"
          aria-haspopup="listbox"
          aria-expanded="false"
          aria-autocomplete="list"
          aria-controls="${this._listboxId}"
          autocomplete="off"
          type="text"
        />
        <button class="clear hidden" part="clear" type="button" tabindex="-1">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M12 4 8 8l4 4-1 1-4-4-4 4-1-1 4-4-4-4 1-1 4 4 4-4z"/>
          </svg>
        </button>
        <button class="toggle" part="toggle" type="button" tabindex="-1">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M8 10.5 3 5.5h10z"/>
          </svg>
        </button>
      </div>
      <div class="popup" part="popup">
        <div class="listbox" part="listbox" id="${this._listboxId}" role="listbox"></div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._input = this.$(".input")
    this._popup = this.$(".popup")
    this._listbox = this.$(".listbox")
    this._clearBtn = this.$(".clear")
    this._toggleBtn = this.$(".toggle")
    this._wrapper = this.$(".wrapper")

    this._clearBtn.setAttribute("aria-label", t("core.clear"))
    this._toggleBtn.setAttribute("aria-label", t("mj.combobox.toggleSuggestions"))

    /* An empty prefix wrapper takes no room (see _syncPrefix). */
    this._syncPrefix()
    const prefixSlot = this.$("[part='prefix'] slot")
    if (prefixSlot !== null) {
      this.listen(prefixSlot, "slotchange", this._syncPrefix.bind(this))
    }

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this._input, "focus", this._syncAccessibleName.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(this._toggleBtn, "click", this._onToggleClick.bind(this))

    /* Pressing a button or an option must not take focus out of the input. */
    this.listen(this._clearBtn, "mousedown", this._keepInputFocus.bind(this))
    this.listen(this._toggleBtn, "mousedown", this._keepInputFocus.bind(this))
    this.listen(this._popup, "mousedown", this._keepInputFocus.bind(this))

    /* One delegated pair of listeners serves every option row. */
    this.listen(this._listbox, "click", this._onOptionClick.bind(this))
    this.listen(this._listbox, "mouseover", this._onOptionHover.bind(this))

    this.listen(this, "click", this._onHostClick.bind(this))
    this.listen(document, "click", this._onDocClick.bind(this))

    this._observeOptions()
    this._buildOptions()

    /* Show the state held in the fields: first render and re-insertion alike. */
    if (this._editing === false) {
      this._inputValue = this._labelForValue(this._value)
    }
    this._input.value = this._inputValue
    this._input.placeholder = this.getAttribute("placeholder") || ""

    this._syncClearBtn()
    this._syncState()
    this._syncAccessibleName()
    this._syncOpen()
    return
  }

  /*
   * The prefix wrapper is shown only while its slot has content: an empty one
   * would still take its padding and indent the input text.
   */
  _syncPrefix() {
    const wrapper = this.$("[part='prefix']")
    if (wrapper !== null) {
      const slot = wrapper.querySelector("slot")
      const assigned = slot !== null ? slot.assignedNodes({ flatten: true }) : []
      wrapper.hidden = assigned.length === 0
    }
    return
  }

  onDisconnected() {
    this._cancelPendingWork()
    this._stopPositioning()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._isReplayedValue(newValue) === false) {
      this._applyValue(newValue || "")
    }
    if (name === "open") {
      this._syncOpen()
    }
    if (name === "disabled" || name === "readonly" || name === "invalid" || name === "required") {
      this._syncState()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    if (name === "placeholder" && this._input !== undefined && this._input !== null) {
      this._input.placeholder = newValue || ""
    }
    if (name === "clearable") {
      this._syncClearBtn()
    }
    if (name === "src") {
      this._remoteOptions = null
      this._loadState = "idle"
    }
    if (name === "label" || name === "aria-label" || name === "aria-labelledby") {
      this._syncAccessibleName()
    }
    return
  }

  /*
   * The base class delivers an attribute change that arrived before the first
   * render a second time once the shadow DOM exists. For `value` the first
   * delivery already stored the value, and applying it again would discard a
   * `value` property assigned in between. Returns true for that repeat.
   */
  _isReplayedValue(newValue) {
    let replayed = false

    if (this._rendered === false) {
      this._preRenderValue = { value: newValue }
    } else if (this._preRenderValue !== null) {
      replayed = this._preRenderValue.value === newValue
      this._preRenderValue = null
    }

    return replayed
  }

  /* Disabled by its own attribute or by an ancestor <fieldset disabled>. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  /* The user may change the text and the value. */
  _canEdit() {
    const editable = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return editable
  }

  /* ----- options ----- */

  _getOptionEls() {
    const els = Array.from(this.querySelectorAll("mj-option"))
    return els
  }

  /*
   * Follow the <mj-option> children: a consumer answering `mj-filter` swaps
   * them for the matches it fetched, and they must reach the open popup.
   */
  _observeOptions() {
    if (typeof MutationObserver !== "function") {
      return
    }
    const observer = new MutationObserver((records) => {
      this._onOptionsMutated(records)
    })
    observer.observe(this, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: OPTION_ATTRIBUTES
    })
    this.onTeardown(() => {
      observer.disconnect()
    })
    return
  }

  _onOptionsMutated(records) {
    const relevant = records.some((record) => {
      return record.type !== "attributes" || record.target !== this
    })
    if (relevant === false || this._input === undefined || this._input === null) {
      return
    }

    this._buildOptions()

    /* The label for the committed value may only be known now. */
    if (this._editing === false) {
      this._showCommittedText()
    }
    if (this.hasAttribute("open") === true) {
      this._renderOptions()
    }
    return
  }

  _buildOptions() {
    const els = this._getOptionEls()
    this._optionData = els.map((el, idx) => {
      const label = el.getAttribute("label") || el.textContent.trim()
      const item = {
        id: nextId("mj-cb-opt"),
        value: el.hasAttribute("value") === true ? el.getAttribute("value") : label,
        label: label,
        disabled: el.hasAttribute("disabled"),
        index: idx,
        el: el
      }
      return item
    })
    return
  }

  /* Turn the items an async source returned into option records. */
  _normaliseRemoteItems(result) {
    let rawItems = []
    if (Array.isArray(result) === true) {
      rawItems = result
    } else if (result !== null && result !== undefined && Array.isArray(result.items) === true) {
      rawItems = result.items
    }

    const items = rawItems.map((raw, idx) => {
      const isObject = raw !== null && typeof raw === "object"
      const value = isObject === true ? raw.value : raw
      const label = isObject === true && raw.label !== undefined && raw.label !== null ? raw.label : value
      const item = {
        id: nextId("mj-cb-opt"),
        value: value === null || value === undefined ? "" : String(value),
        label: label === null || label === undefined ? "" : String(label),
        disabled: isObject === true && raw.disabled === true,
        index: idx,
        el: null,
        data: raw
      }
      return item
    })
    return items
  }

  _usesRemote() {
    const src = this.getAttribute("src") || ""
    const remote = this._dataSource !== null || src.length > 0
    return remote
  }

  /* The options the popup can currently draw from. */
  _sourceOptions() {
    let options = this._optionData
    if (this._usesRemote() === true && this._remoteOptions !== null) {
      options = this._remoteOptions
    }
    return options
  }

  _labelForValue(val) {
    let label = val

    const match = this._sourceOptions().find((item) => item.value === val)
    if (match !== undefined) {
      label = match.label
    } else if (this._valueLabel !== null && this._valueLabel.value === val) {
      label = this._valueLabel.label
    }

    return label
  }

  /* The text the user typed, or "" when the input still shows the committed label. */
  _query() {
    const query = this._editing === true ? this._inputValue : ""
    return query
  }

  _filteredOptions(query) {
    const source = this._sourceOptions()
    let filtered = source

    if (typeof this._filterFn === "function") {
      filtered = source.filter((item) => {
        const subject = item.el !== null ? item.el : item.data
        return this._filterFn(subject, query) === true
      })
    } else if (this._usesRemote() === false && query.length > 0) {
      /* Remote sources filter on their side; local options by label. */
      const needle = query.toLowerCase()
      filtered = source.filter((item) => item.label.toLowerCase().includes(needle))
    }

    return filtered
  }

  _optionNodes() {
    const nodes = Array.from(this._listbox.querySelectorAll(".option"))
    return nodes
  }

  /* A status row (no results, loading, error) whose text a slot can replace. */
  _buildStatusRow(className, slotName, fallbackText) {
    const row = document.createElement("div")
    row.className = className
    row.setAttribute("part", className)
    const slot = document.createElement("slot")
    slot.name = slotName
    slot.textContent = fallbackText
    row.appendChild(slot)
    return row
  }

  /*
   * Fill `labelEl` with `label`, wrapping the part that matches `query` in a
   * <mark>. Built from text nodes: labels are application data. The <mark>
   * is not aria-hidden -- hiding it would cut the typed letters out of the
   * option's accessible name.
   */
  _fillLabel(labelEl, label, query) {
    const matchAt = query.length > 0 ? label.toLowerCase().indexOf(query.toLowerCase()) : -1

    if (matchAt < 0) {
      labelEl.textContent = label
      return
    }

    const mark = document.createElement("mark")
    mark.setAttribute("part", "option-match")
    mark.textContent = label.slice(matchAt, matchAt + query.length)

    labelEl.appendChild(document.createTextNode(label.slice(0, matchAt)))
    labelEl.appendChild(mark)
    labelEl.appendChild(document.createTextNode(label.slice(matchAt + query.length)))
    return
  }

  _renderOptions() {
    const query = this._query()

    this._listbox.replaceChildren()
    this._visibleItems = []
    this._focusedIndex = -1
    this._input.removeAttribute("aria-activedescendant")

    if (this._loadState === "loading") {
      const row = this._buildStatusRow("loading", "loading", t("core.loading"))
      row.setAttribute("aria-busy", "true")
      this._listbox.appendChild(row)
      return
    }

    if (this._loadState === "error") {
      const row = this._buildStatusRow("error-inline", "error", t("mj.combobox.loadError"))
      this._listbox.appendChild(row)
      return
    }

    const filtered = this._filteredOptions(query)
    if (filtered.length === 0) {
      const row = this._buildStatusRow("no-results", "no-results", t("core.noResults"))
      this._listbox.appendChild(row)
      return
    }

    this._visibleItems = filtered
    filtered.forEach((item, position) => {
      const node = document.createElement("div")
      node.className = "option"
      node.setAttribute("part", "option")
      node.setAttribute("role", "option")
      node.id = item.id
      node.dataset.position = String(position)
      node.setAttribute("aria-selected", item.value === this._value ? "true" : "false")
      if (item.disabled === true) {
        node.setAttribute("aria-disabled", "true")
      }

      const labelEl = document.createElement("span")
      labelEl.className = "option-label"
      labelEl.setAttribute("part", "option-label")
      this._fillLabel(labelEl, item.label, query)
      node.appendChild(labelEl)

      this._listbox.appendChild(node)
    })
    return
  }

  /* ----- async suggestions ----- */

  /*
   * Ask the data source (or `src`) for the options matching `query`. Each
   * request carries a sequence number; a response that is no longer the
   * latest is dropped, and a superseded fetch is aborted.
   */
  _loadRemote(query) {
    this._loadToken = this._loadToken + 1
    const token = this._loadToken

    if (this._abortController !== null) {
      this._abortController.abort()
      this._abortController = null
    }

    this._loadState = "loading"
    this._renderOptions()

    let pending = null
    if (this._dataSource !== null) {
      try {
        pending = Promise.resolve(this._dataSource.query(query))
      } catch (error) {
        pending = Promise.reject(error)
      }
    } else {
      const src = this.getAttribute("src") || ""
      const separator = src.includes("?") === true ? "&" : "?"
      const url = `${src}${separator}q=${encodeURIComponent(query)}`
      const controller = new AbortController()
      this._abortController = controller
      pending = fetch(url, { signal: controller.signal }).then((response) => {
        if (response.ok === false) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.json()
      })
    }

    pending
      .then((result) => {
        if (token !== this._loadToken) {
          return
        }
        this._remoteOptions = this._normaliseRemoteItems(result)
        this._loadState = "idle"
        if (this.hasAttribute("open") === true) {
          this._renderOptions()
        }
        const results = this._visibleItems.map((item) => item.data)
        this.emit("mj-filter", { query: query, results: results })
        if (results.length === 0) {
          announce(t("core.noResults"), "polite")
        }
      })
      .catch((error) => {
        if (token !== this._loadToken || (error !== null && error !== undefined && error.name === "AbortError")) {
          return
        }
        this._remoteOptions = []
        this._loadState = "error"
        if (this.hasAttribute("open") === true) {
          this._renderOptions()
        }
        this.emit("mj-error", { error: error })
        announce(t("mj.combobox.loadError"), "assertive")
      })
    return
  }

  /* Stop the debounce timer and forget any request still in flight. */
  _cancelPendingWork() {
    clearTimeout(this._debounceTimer)
    this._debounceTimer = null

    this._loadToken = this._loadToken + 1
    if (this._abortController !== null) {
      this._abortController.abort()
      this._abortController = null
    }
    if (this._loadState === "loading") {
      /* The answer never arrived: the next open asks again. */
      this._loadState = "idle"
      this._remoteOptions = null
    }
    return
  }

  /* ----- open/close ----- */

  _stopPositioning() {
    if (this._disposePosition !== null) {
      this._disposePosition()
      this._disposePosition = null
    }
    return
  }

  _open() {
    if (this._canEdit() === false) {
      return
    }
    if (this.hasAttribute("open") === true) {
      return
    }
    const proceed = this.emit("mj-open", {}, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.setAttribute("open", "")
    return
  }

  /*
   * Close the popup. Anything that would reopen it later -- the debounce
   * timer, a request in flight -- is cancelled here as well.
   */
  _close() {
    this._cancelPendingWork()
    if (this._loadState === "error") {
      /* Reopening retries the request instead of showing the stale error. */
      this._loadState = "idle"
      this._remoteOptions = null
    }
    if (this.hasAttribute("open") === false) {
      return
    }
    this.removeAttribute("open")
    this.emit("mj-close", {})
    return
  }

  /*
   * Bring the popup and the input's ARIA state in line with the `open`
   * attribute. Safe to call repeatedly: the positioner is replaced, never
   * stacked.
   */
  _syncOpen() {
    if (this._input === undefined || this._input === null) {
      return
    }

    const isOpen = this.hasAttribute("open")
    this._input.setAttribute("aria-expanded", isOpen === true ? "true" : "false")
    this._stopPositioning()

    if (isOpen === true) {
      this._popup.style.setProperty("--_anchor-width", `${this._wrapper.offsetWidth}px`)
      this._disposePosition = autoPosition(this._popup, this._wrapper, {
        placement: "bottom-start"
      })
      if (this._usesRemote() === true && this._remoteOptions === null && this._loadState === "idle") {
        this._loadRemote(this._query())
      } else {
        this._renderOptions()
      }
    } else {
      this._focusedIndex = -1
      this._input.removeAttribute("aria-activedescendant")
    }
    return
  }

  _syncClearBtn() {
    if (this._clearBtn === undefined || this._clearBtn === null) {
      return
    }
    const hasValue = this._value.length > 0 || this._inputValue.length > 0
    const clearable = this.hasAttribute("clearable")
    if (clearable === true && hasValue === true && this._canEdit() === true) {
      this._clearBtn.classList.remove("hidden")
    } else {
      this._clearBtn.classList.add("hidden")
    }
    return
  }

  /* Mirror disabled / readonly / invalid / required onto the inner controls. */
  _syncState() {
    if (this._input === undefined || this._input === null) {
      return
    }

    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")

    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._clearBtn.disabled = disabled === true || readonly === true
    this._toggleBtn.disabled = disabled === true || readonly === true
    this._wrapper.classList.toggle("is-disabled", disabled)

    if (this.hasAttribute("invalid") === true || this._isUserInvalid() === true) {
      this._input.setAttribute("aria-invalid", "true")
    } else {
      this._input.removeAttribute("aria-invalid")
    }
    if (this.hasAttribute("required") === true) {
      this._input.setAttribute("aria-required", "true")
    } else {
      this._input.removeAttribute("aria-required")
    }

    this._syncClearBtn()
    if (this._canEdit() === false) {
      this._close()
    }
    return
  }

  /* ----- accessible name ----- */

  /*
   * The text that names the combobox: the `label` attribute, then the host's
   * `aria-label`, then the elements named by the host's `aria-labelledby`,
   * then any <label> associated with the host (wrapping or `for`).
   */
  _computeAccessibleName() {
    const labelAttr = (this.getAttribute("label") || "").trim()
    if (labelAttr.length > 0) {
      return labelAttr
    }
    const ariaLabel = (this.getAttribute("aria-label") || "").trim()
    if (ariaLabel.length > 0) {
      return ariaLabel
    }
    const labelledBy = (this.getAttribute("aria-labelledby") || "").trim()
    if (labelledBy.length > 0) {
      const root = this.getRootNode()
      const texts = []
      labelledBy.split(/\s+/).forEach((id) => {
        const target = typeof root.getElementById === "function" ? root.getElementById(id) : null
        if (target !== null) {
          texts.push(textExcluding(target, this))
        }
      })
      const joined = texts.filter((text) => text.length > 0).join(" ")
      if (joined.length > 0) {
        return joined
      }
    }
    let labels = []
    try {
      labels = this._internals !== null && this._internals.labels ? Array.from(this._internals.labels) : []
    } catch (error) {
      labels = []
    }
    const rtnval = labels
      .map((labelEl) => textExcluding(labelEl, this))
      .filter((text) => text.length > 0)
      .join(" ")
    return rtnval
  }

  _syncAccessibleName() {
    if (this._input === undefined || this._input === null) {
      return
    }
    const name = this._computeAccessibleName()
    if (name.length > 0) {
      this._input.setAttribute("aria-label", name)
      this._listbox.setAttribute("aria-label", name)
    } else {
      this._input.removeAttribute("aria-label")
      this._listbox.removeAttribute("aria-label")
    }
    return
  }

  /* ----- value ----- */

  /* Put the label of the committed value back into the input. */
  _showCommittedText() {
    this._inputValue = this._labelForValue(this._value)
    this._editing = false
    if (this._input !== undefined && this._input !== null) {
      this._input.value = this._inputValue
    }
    this._syncClearBtn()
    return
  }

  /*
   * Set the value without reporting a change: the `value` attribute and
   * property, form reset and restore.
   */
  _applyValue(value) {
    const normalized = value === null || value === undefined ? "" : String(value)
    this._setFormValue(normalized)
    this._showCommittedText()
    if (this._listbox !== undefined && this._listbox !== null && this.hasAttribute("open") === true) {
      this._renderOptions()
    }
    return
  }

  /*
   * Commit a value chosen by the user. `label` is what the input shows for
   * it and `optionEl` the <mj-option> it came from (null for free text, a
   * remote item or a clear). mj-change fires only when the value differs.
   */
  _commit(value, label, optionEl) {
    const previousValue = this._value

    this._valueLabel = { value: value, label: label }
    this._setFormValue(value)
    this._inputValue = label
    this._input.value = label
    this._editing = false
    this._syncClearBtn()

    if (value !== previousValue) {
      this.emit("mj-change", { value: value, previousValue: previousValue, option: optionEl })
    }
    return
  }

  _commitItem(item) {
    if (item === undefined || item === null || item.disabled === true) {
      return
    }
    if (this._canEdit() === false) {
      return
    }
    this._commit(item.value, item.label, item.el)
    this._close()
    return
  }

  /*
   * Settle text the user typed without picking a suggestion: an exact label
   * match becomes that option, free-text mode keeps the text as the value,
   * anything else goes back to the committed value. Empty text clears.
   */
  _commitTyped() {
    if (this._canEdit() === false || this._editing === false) {
      return
    }

    const text = this._inputValue.trim()
    if (text.length === 0) {
      this._commit("", "", null)
      return
    }

    const needle = text.toLowerCase()
    const exact = this._sourceOptions().find((item) => {
      return item.disabled !== true && item.label.toLowerCase() === needle
    })

    if (exact !== undefined) {
      this._commit(exact.value, exact.label, exact.el)
    } else if (this.hasAttribute("free-text") === true) {
      this._commit(text, text, null)
    } else {
      this._showCommittedText()
    }
    return
  }

  /* ----- event handlers ----- */

  _keepInputFocus(event) {
    event.preventDefault()
    return
  }

  _onInput(event) {
    this._inputValue = this._input.value
    this._editing = true
    this.emit("mj-input", { inputValue: this._inputValue })
    this._syncClearBtn()

    clearTimeout(this._debounceTimer)
    const delay = readCount(this, "debounce", DEFAULT_DEBOUNCE_MS)
    const minChars = readCount(this, "min-chars", DEFAULT_MIN_CHARS)

    this._debounceTimer = setTimeout(() => {
      this._debounceTimer = null
      if (this._inputValue.length >= minChars) {
        this._showSuggestions()
      } else {
        this._close()
      }
    }, delay)
    return
  }

  /* Open the popup (or refresh it) for the text currently in the input. */
  _showSuggestions() {
    const query = this._query()

    if (this._usesRemote() === true) {
      /* Start from a clean slate so opening does not issue a second request. */
      this._remoteOptions = []
      this._open()
      if (this.hasAttribute("open") === true) {
        this._loadRemote(query)
      }
      return
    }

    if (this.hasAttribute("open") === true) {
      this._renderOptions()
    } else {
      this._open()
    }

    if (this.hasAttribute("open") === true) {
      const results = this._visibleItems.map((item) => item.el)
      this.emit("mj-filter", { query: query, results: results })
      if (results.length === 0) {
        announce(t("core.noResults"), "polite")
      }
    }
    return
  }

  /* Index of the nearest enabled row from `from` in direction `delta`, or -1. */
  _nextEnabledPosition(from, delta) {
    const count = this._visibleItems.length
    let found = -1
    let position = from + delta

    while (position >= 0 && position < count) {
      if (this._visibleItems[position].disabled !== true) {
        found = position
        break
      }
      position = position + delta
    }

    return found
  }

  _onKeydown(event) {
    const isOpen = this.hasAttribute("open")
    const count = this._visibleItems.length

    /* Alt+Arrow is tested first: the plain arrow branches would swallow it. */
    if (event.altKey === true && event.key === "ArrowDown") {
      event.preventDefault()
      this._open()
    } else if (event.altKey === true && event.key === "ArrowUp") {
      event.preventDefault()
      this._close()
    } else if (event.key === "ArrowDown") {
      event.preventDefault()
      if (isOpen === false) {
        this._open()
      }
      if (this.hasAttribute("open") === true) {
        this._setFocused(this._nextEnabledPosition(this._focusedIndex, 1))
      }
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      if (isOpen === true) {
        const from = this._focusedIndex >= 0 ? this._focusedIndex : count
        this._setFocused(this._nextEnabledPosition(from, -1))
      }
    } else if (event.key === "Home" && isOpen === true && this._focusedIndex >= 0) {
      event.preventDefault()
      this._setFocused(this._nextEnabledPosition(-1, 1))
    } else if (event.key === "End" && isOpen === true && this._focusedIndex >= 0) {
      event.preventDefault()
      this._setFocused(this._nextEnabledPosition(count, -1))
    } else if (event.key === "Enter") {
      if (isOpen === true && this._focusedIndex >= 0) {
        event.preventDefault()
        this._commitItem(this._visibleItems[this._focusedIndex])
      } else if (this._editing === true) {
        event.preventDefault()
        this._commitTyped()
        this._close()
      }
    } else if (event.key === "Escape") {
      if (isOpen === true) {
        /* Only an Escape that closed the popup is consumed (core/overlay.js
           then keeps an enclosing dialog from closing on the same key). */
        event.preventDefault()
      }
      this._showCommittedText()
      this._close()
    }
    return
  }

  /* Make the row at `position` the active descendant; -1 leaves it unchanged. */
  _setFocused(position) {
    if (position < 0) {
      return
    }

    const nodes = this._optionNodes()
    const node = nodes[position]
    if (node === undefined) {
      return
    }

    nodes.forEach((other) => other.classList.remove("focused"))
    node.classList.add("focused")
    node.scrollIntoView({ block: "nearest" })
    this._focusedIndex = position
    this._input.setAttribute("aria-activedescendant", node.id)
    return
  }

  _optionNodeFor(event) {
    const target = event.target instanceof Element ? event.target.closest(".option") : null
    return target
  }

  _onOptionClick(event) {
    const node = this._optionNodeFor(event)
    if (node === null) {
      return
    }
    const position = parseInt(node.dataset.position, 10)
    this._commitItem(this._visibleItems[position])
    this._input.focus()
    return
  }

  _onOptionHover(event) {
    const node = this._optionNodeFor(event)
    if (node === null || node.getAttribute("aria-disabled") === "true") {
      return
    }
    const position = parseInt(node.dataset.position, 10)
    if (position !== this._focusedIndex) {
      this._setFocused(position)
    }
    return
  }

  /*
   * Focus left the input. Unless it only moved to another part of this
   * control, the text and the value are reconciled and the popup closes.
   */
  _onBlur(event) {
    const next = event.relatedTarget
    const staysInside = next instanceof Node && this.shadowRoot.contains(next) === true
    if (staysInside === true) {
      return
    }
    this._commitTyped()
    this._close()
    return
  }

  _onClear() {
    if (this._canEdit() === false) {
      return
    }
    this._commit("", "", null)
    this.emit("mj-clear", {})
    this._close()
    this._input.focus()
    return
  }

  _onToggleClick() {
    if (this.hasAttribute("open") === true) {
      this._close()
    } else {
      this._open()
    }
    this._input.focus()
    return
  }

  /*
   * A click aimed at the host itself (not at a control inside it) is what an
   * associated <label> dispatches when it is clicked: move focus to the
   * input the way a native control would.
   */
  _onHostClick(event) {
    const origin = event.composedPath()[0]
    if (origin === this && this._input !== undefined && this._input !== null) {
      this._input.focus()
    }
    return
  }

  _onDocClick(event) {
    if (this.hasAttribute("open") === false) {
      return
    }
    const inside = event.composedPath().includes(this)
    if (inside === false) {
      this._commitTyped()
      this._close()
    }
    return
  }

  /*
   * FormControlMixin hooks: a failed validation (an mj-form submit) marks the
   * control invalid, as the `invalid` attribute does, until it is valid again.
   */
  onInvalid(message) {
    if (this._input !== undefined && this._input !== null) {
      this._syncState()
    }
    return
  }

  onValidityRestored() {
    if (this._input !== undefined && this._input !== null) {
      this._syncState()
    }
    return
  }

  _validationAnchor() {
    return this._input || this
  }

  /* ----- form callbacks ----- */

  /* The base class has already restored the form value; show it. */
  onFormReset(initial) {
    this._showCommittedText()
    return
  }

  onFormRestore(state) {
    this._showCommittedText()
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncState()
    return
  }

  /* ----- scriptable API ----- */

  /*
   * Assigning `value` updates the input text as well as the submitted form
   * value. The `value` attribute keeps the default for form reset.
   */
  get value() {
    return this._value
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  get inputValue() {
    return this._inputValue
  }

  /* The <mj-option> elements behind the rows currently shown (sync options). */
  get options() {
    const shown = this._visibleItems.filter((item) => item.el !== null).map((item) => item.el)
    return shown
  }

  get dataSource() {
    return this._dataSource
  }

  set dataSource(source) {
    this._dataSource = source === undefined ? null : source
    this._remoteOptions = null
    this._loadState = "idle"
    return
  }

  get filterFn() {
    return this._filterFn
  }

  set filterFn(fn) {
    this._filterFn = typeof fn === "function" ? fn : null
    if (this._listbox !== undefined && this._listbox !== null && this.hasAttribute("open") === true) {
      this._renderOptions()
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    if (value === true) {
      this._open()
    } else {
      this._close()
    }
    return
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus()
    }
    return
  }
}
