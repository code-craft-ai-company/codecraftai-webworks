/*
 * mjcascadingselect.js
 *
 * <mj-cascading-select> — ordered chain of dependent selects where each
 * level's options depend on the previous level's selection.
 *
 * The `levels` property configures the chain. Each level config is
 *   { name, label, placeholder, options, src, dataSource }
 * and its options come from, in order of precedence:
 *   - `options` as a function `(parentValue, parentValues) => items` (the
 *     result may be a promise);
 *   - `options` as a lookup object `{ [parentValue]: items }`;
 *   - `src`, a URL whose `{parentValue}` token is replaced and fetched;
 *   - `dataSource`, an object whose `query({ filter: parentValue })`
 *     resolves to the items (or `{ items }`);
 *   - `options` as a plain array, used whatever the parent value is.
 * Items are `{ value, label }` objects or plain strings.
 *
 * The level controls are built once per `levels` assignment and updated in
 * place afterwards, so the select the user is operating keeps keyboard
 * focus. State lives in fields (`_levelValues`, `_levelOptions`,
 * `_levelStates`) and the DOM is rebuilt from them after a re-insert.
 *
 * Form value: the JSON array of level values under the host `name`; when
 * level configs carry a `name`, each of those levels also submits its own
 * `name=value` entry. The `value` attribute (a JSON array) is the default a
 * form reset restores; the `value` property reads that JSON and, assigned
 * (JSON text or an array), sets the levels like `values` does.
 *
 * The `level-loading` and `level-error` slots exist once each and are moved
 * into the level that is loading / failed: a named slot repeated in a shadow
 * tree only receives content in its first occurrence. One level at most is
 * in either state, because the walk over the levels stops at a pending load.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";

const STYLES = `
:host { display: block; }

.levels {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-cascading-select-gap, var(--mj-space-3));
}
:host([orientation="vertical"]) .levels { flex-direction: column; }

.level {
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
  min-width: var(--mj-cascading-select-level-min-width, 10rem);
  flex: 1;
}

.level-label {
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}

.level-select {
  width: 100%;
  min-height: var(--mj-control-height-md);
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: pointer;
}
.level-select:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.level-select:disabled { opacity: 0.55; cursor: not-allowed; }
.level-select[aria-invalid="true"] { border-color: var(--mj-color-danger); }

:host([size="sm"]) .level-select { min-height: var(--mj-control-height-sm); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .level-select { min-height: var(--mj-control-height-lg); font-size: var(--mj-font-size-lg); }

.level-loading {
  height: var(--mj-cascading-select-level-loading-height, var(--mj-control-height-md));
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-md);
  animation: mj-pulse 1.4s ease infinite;
}
@keyframes mj-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.level-error {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  color: var(--mj-color-danger);
  font-size: var(--mj-font-size-sm);
  padding: var(--mj-space-1) 0;
}
.level-retry {
  font: inherit;
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-sm);
  padding: 0 var(--mj-space-2);
  cursor: pointer;
}
.level-retry:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
`;

/* Turn whatever a level source produced into [{ value, label }] records. */
function normaliseOptions(result) {
  let rawItems = []
  if (Array.isArray(result) === true) {
    rawItems = result
  } else if (result !== null && result !== undefined && Array.isArray(result.items) === true) {
    rawItems = result.items
  }

  const options = rawItems.map((raw) => {
    const isObject = raw !== null && typeof raw === "object"
    const value = isObject === true ? raw.value : raw
    const label = isObject === true && raw.label !== undefined && raw.label !== null ? raw.label : value
    const option = {
      value: value === null || value === undefined ? "" : String(value),
      label: label === null || label === undefined ? "" : String(label)
    }
    return option
  })
  return options
}

/* Parse the `value` attribute / a restored form state: a JSON array of strings. */
function parseValueList(text) {
  let list = []
  if (typeof text === "string" && text.trim().length > 0) {
    try {
      const parsed = JSON.parse(text)
      if (Array.isArray(parsed) === true) {
        list = parsed
      }
    } catch (error) {
      list = []
    }
  }
  return list
}

export class MjCascadingSelect extends FormControlMixin(MjElement) {
  static tagName = "mj-cascading-select";
  static styles = STYLES;
  static watched = [
    "value", "name", "disabled", "required", "invalid", "orientation", "size", "label", "aria-label"
  ];

  constructor() {
    super()
    this._initFormControl()
    this._levelConfig = []
    this._levelValues = []
    this._levelStates = []   /* "idle" | "loading" | "error" */
    this._levelOptions = []  /* arrays of {value, label} per level */

    /* Per level: sequence number of the latest load, and its fetch controller. */
    this._loadTokens = []
    this._abortControllers = []

    /* Per level: the shadow nodes built by _buildLevels(). */
    this._levelNodes = []

    /* The single level-loading / level-error slots (see header), built with the levels. */
    this._loadingSlot = null
    this._errorSlot = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* The `value` attribute change applied before the first render, if any. */
    this._preRenderValue = null
  }

  render() {
    const markup = `<div class="levels" part="levels" role="group"></div>`
    return markup
  }

  afterRender() {
    this._levelsEl = this.$(".levels")

    /* One delegated listener each, however often the levels are rebuilt. */
    this.listen(this._levelsEl, "change", this._onLevelChange.bind(this))
    this.listen(this._levelsEl, "click", this._onLevelsClick.bind(this))

    this._buildLevels()
    this._syncGroup()

    /*
     * A load that was running when the element was removed was aborted in
     * onDisconnected(); start again from the first level left waiting.
     */
    const interrupted = this._levelStates.indexOf("loading")
    if (interrupted >= 0) {
      this._resolveFrom(interrupted)
    } else {
      this._syncAllLevels()
    }
    return
  }

  onDisconnected() {
    for (let index = 0; index < this._levelConfig.length; index = index + 1) {
      this._cancelLoad(index)
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value" && this._isReplayedValue(newValue) === false) {
      this._applyValues(parseValueList(newValue))
    }
    if (name === "name") {
      this._syncFormValue()
    }
    if (name === "disabled" || name === "invalid") {
      this._syncAllLevels()
    }
    if (name === "disabled" || name === "label" || name === "aria-label") {
      this._syncGroup()
    }
    if (name === "required" && this._internals !== undefined) {
      this._refreshValidity()
    }
    return
  }

  /*
   * The base class delivers an attribute change that arrived before the first
   * render a second time once the shadow DOM exists. For `value` the first
   * delivery already stored the values, and applying it again would discard
   * a `values` assignment made in between. Returns true for that repeat.
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

  /* ----- public API: set levels config ----- */

  get levels() {
    return this._levelConfig
  }

  /*
   * Assign the level configuration. Values already chosen are kept for the
   * levels whose new options still contain them, so a consumer may refresh
   * the configuration without wiping the user's progress.
   */
  set levels(configs) {
    for (let index = 0; index < this._levelConfig.length; index = index + 1) {
      this._cancelLoad(index)
    }

    this._levelConfig = Array.isArray(configs) === true ? configs : []
    const count = this._levelConfig.length
    const previousValues = this._levelValues

    this._levelValues = []
    this._levelStates = []
    this._levelOptions = []
    for (let index = 0; index < count; index = index + 1) {
      const kept = previousValues[index]
      this._levelValues.push(typeof kept === "string" ? kept : "")
      this._levelStates.push("idle")
      this._levelOptions.push([])
      if (this._loadTokens[index] === undefined) {
        this._loadTokens[index] = 0
      }
    }

    this._buildLevels()
    this._resolveFrom(0)
    return
  }

  get values() {
    return this._levelValues.slice()
  }

  /* The submitted JSON array of level values ("" while no levels are configured). */
  get value() {
    return this._value
  }

  /*
   * Assigning `value` (JSON array text, or an array) selects the levels like
   * `values` does; the `value` attribute keeps the default for form reset.
   */
  set value(next) {
    const list = Array.isArray(next) === true ? next : parseValueList(next)
    this._applyValues(list)
    return
  }

  /*
   * Pre-populate the chain. Levels are settled in order: each level's
   * options are resolved (loading them when they are async) before its value
   * is checked and the next level is looked at.
   */
  set values(vals) {
    this._applyValues(vals)
    return
  }

  _applyValues(vals) {
    const list = Array.isArray(vals) === true ? vals : []
    const count = this._levelConfig.length
    const wanted = count > 0 ? count : list.length

    this._levelValues = []
    for (let index = 0; index < wanted; index = index + 1) {
      const value = list[index]
      this._levelValues.push(value === null || value === undefined ? "" : String(value))
    }

    this._resolveFrom(0)
    return
  }

  /* ----- option resolution ----- */

  /* Forget the load in flight for a level: its answer will be ignored. */
  _cancelLoad(index) {
    this._loadTokens[index] = (this._loadTokens[index] || 0) + 1
    const controller = this._abortControllers[index]
    if (controller !== undefined && controller !== null) {
      controller.abort()
    }
    this._abortControllers[index] = null
    return
  }

  /* Drop the value of `index` and of every level after it. */
  _clearValuesFrom(index) {
    for (let later = index; later < this._levelValues.length; later = later + 1) {
      this._levelValues[later] = ""
    }
    return
  }

  /* A value that is not among the level's options cannot stay selected. */
  _validateLevelValue(index) {
    const value = this._levelValues[index] || ""
    if (value.length === 0) {
      return
    }
    const options = this._levelOptions[index] || []
    const known = options.some((option) => option.value === value)
    if (known === false) {
      this._clearValuesFrom(index)
    }
    return
  }

  /*
   * Settle the levels from `startIndex` on, in order. A level whose options
   * load asynchronously stops the walk; it continues from the next level
   * when the load completes (see _finishLoad).
   */
  _resolveFrom(startIndex) {
    const count = this._levelConfig.length
    let index = startIndex
    let waiting = false

    while (index < count && waiting === false) {
      waiting = this._resolveLevel(index)
      index = index + 1
    }

    /* Levels behind a pending load have no options until it completes. */
    for (let later = index; later < count; later = later + 1) {
      this._cancelLoad(later)
      this._levelOptions[later] = []
      this._levelStates[later] = "idle"
    }

    this._syncAllLevels()
    this._syncFormValue()
    return
  }

  /*
   * Work out the options of one level from its config and its parent value.
   * Returns true when the options are being loaded asynchronously.
   */
  _resolveLevel(index) {
    const cfg = this._levelConfig[index] || {}
    const parentValue = index > 0 ? (this._levelValues[index - 1] || "") : ""
    let pending = false

    this._cancelLoad(index)
    this._levelStates[index] = "idle"

    if (index > 0 && parentValue.length === 0) {
      /* Nothing chosen upstream: the level is empty and waits. */
      this._levelOptions[index] = Array.isArray(cfg.options) === true ? normaliseOptions(cfg.options) : []
      this._levelValues[index] = ""
      return pending
    }

    const optionsKind = typeof cfg.options
    const isLookup =
      cfg.options !== null && optionsKind === "object" && Array.isArray(cfg.options) === false

    if (optionsKind === "function") {
      const parentValues = this._levelValues.slice(0, index)
      let result = null
      try {
        result = cfg.options(parentValue, parentValues)
      } catch (error) {
        result = Promise.reject(error)
      }
      if (result !== null && result !== undefined && typeof result.then === "function") {
        this._startLoad(index, parentValue, result)
        pending = true
      } else {
        this._levelOptions[index] = normaliseOptions(result)
      }
    } else if (isLookup === true) {
      this._levelOptions[index] = normaliseOptions(cfg.options[parentValue])
    } else if (typeof cfg.src === "string" && cfg.src.length > 0) {
      const url = cfg.src.split("{parentValue}").join(encodeURIComponent(parentValue))
      const controller = new AbortController()
      this._abortControllers[index] = controller
      const request = fetch(url, { signal: controller.signal }).then((response) => {
        if (response.ok === false) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.json()
      })
      this._startLoad(index, parentValue, request)
      pending = true
    } else if (cfg.dataSource !== null && cfg.dataSource !== undefined) {
      let request = null
      try {
        request = Promise.resolve(cfg.dataSource.query({ filter: parentValue }))
      } catch (error) {
        request = Promise.reject(error)
      }
      this._startLoad(index, parentValue, request)
      pending = true
    } else {
      this._levelOptions[index] = normaliseOptions(cfg.options)
    }

    if (pending === false) {
      this._validateLevelValue(index)
    }
    return pending
  }

  /*
   * Track an asynchronous option load. The load carries the level's current
   * sequence number; when a newer load (or a cancel) has replaced it by the
   * time it settles, its result is dropped.
   */
  _startLoad(index, parentValue, request) {
    const token = this._loadTokens[index]
    const cfg = this._levelConfig[index] || {}

    this._levelStates[index] = "loading"
    this._levelOptions[index] = []
    this.emit("mj-level-load-start", { levelIndex: index, parentValue: parentValue })
    if (typeof cfg.label === "string" && cfg.label.length > 0) {
      announce(t("mj.cascadingSelect.loadingLevel", { label: cfg.label }), "polite")
    }

    request
      .then((result) => {
        if (token !== this._loadTokens[index]) {
          return
        }
        this._finishLoad(index, normaliseOptions(result))
      })
      .catch((error) => {
        const aborted = error !== null && error !== undefined && error.name === "AbortError"
        if (token !== this._loadTokens[index] || aborted === true) {
          return
        }
        this._abortControllers[index] = null
        this._levelStates[index] = "error"
        this.emit("mj-level-error", { levelIndex: index, error: error })
        announce(t("mj.cascadingSelect.loadError"), "assertive")
        this._syncAllLevels()
        this._syncFormValue()
      })
    return
  }

  _finishLoad(index, options) {
    this._abortControllers[index] = null
    this._levelOptions[index] = options
    this._levelStates[index] = "idle"
    this.emit("mj-level-load-end", { levelIndex: index, options: options })

    this._validateLevelValue(index)
    this._resolveFrom(index + 1)
    return
  }

  /* ----- rendering ----- */

  /*
   * Build the controls of every level: label, <select>, loading placeholder
   * and error row. Built with DOM APIs -- labels, placeholders and options
   * are application data and may come from a remote response.
   */
  _buildLevels() {
    if (this._levelsEl === undefined || this._levelsEl === null) {
      return
    }

    /* A rebuild replaces the controls; remember which level had focus. */
    const active = this.shadowRoot.activeElement
    const focusedLevel = active !== null && active.dataset.level !== undefined
      ? parseInt(active.dataset.level, 10)
      : -1

    this._levelsEl.replaceChildren()
    this._levelNodes = []

    this._loadingSlot = document.createElement("slot")
    this._loadingSlot.name = "level-loading"
    this._errorSlot = document.createElement("slot")
    this._errorSlot.name = "level-error"
    this._errorSlot.textContent = t("mj.cascadingSelect.loadError")

    this._levelConfig.forEach((rawConfig, index) => {
      const cfg = rawConfig || {}
      const labelId = nextId("mj-cs-label")
      const labelText = typeof cfg.label === "string" ? cfg.label : ""

      const wrapper = document.createElement("div")
      wrapper.className = "level"
      wrapper.setAttribute("part", "level")

      const label = document.createElement("span")
      label.className = "level-label"
      label.setAttribute("part", "level-label")
      label.id = labelId
      label.textContent = labelText
      wrapper.appendChild(label)

      const select = document.createElement("select")
      select.className = "level-select"
      select.setAttribute("part", "level-select")
      select.dataset.level = String(index)
      if (labelText.length > 0) {
        select.setAttribute("aria-labelledby", labelId)
      } else {
        select.setAttribute("aria-label", cfg.placeholder || cfg.name || t("mj.cascadingSelect.levelLabel", { level: index + 1 }))
      }
      wrapper.appendChild(select)

      const loading = document.createElement("div")
      loading.className = "level-loading"
      loading.setAttribute("part", "level-loading")
      loading.setAttribute("aria-busy", "true")
      loading.dataset.level = String(index)
      loading.tabIndex = -1
      loading.hidden = true
      wrapper.appendChild(loading)

      const error = document.createElement("div")
      error.className = "level-error"
      error.setAttribute("part", "level-error")
      error.setAttribute("role", "alert")
      error.hidden = true
      const errorMessage = document.createElement("span")
      errorMessage.className = "level-error-message"
      errorMessage.textContent = t("mj.cascadingSelect.loadError")
      error.appendChild(errorMessage)
      const retry = document.createElement("button")
      retry.type = "button"
      retry.className = "level-retry"
      retry.setAttribute("part", "level-retry")
      retry.dataset.level = String(index)
      retry.textContent = t("mj.cascadingSelect.retry")
      error.appendChild(retry)
      wrapper.appendChild(error)

      this._levelsEl.appendChild(wrapper)
      this._levelNodes.push({
        wrapper: wrapper,
        select: select,
        loading: loading,
        error: error,
        errorMessage: errorMessage,
        renderedOptions: null
      })
    })

    const refocus = this._levelNodes[focusedLevel]
    if (refocus !== undefined) {
      refocus.select.focus()
    }
    return
  }

  /* Replace the <option> children of a level's select. */
  _fillSelect(select, cfg, options) {
    select.replaceChildren()

    const placeholder = document.createElement("option")
    placeholder.value = ""
    placeholder.textContent = cfg.placeholder || t("mj.cascadingSelect.placeholder")
    select.appendChild(placeholder)

    options.forEach((item) => {
      const option = document.createElement("option")
      option.value = item.value
      option.textContent = item.label
      select.appendChild(option)
    })
    return
  }

  /*
   * Update every level's controls in place from the fields. The <select>
   * elements are never replaced, so the one the user is operating keeps
   * focus; its options are only rewritten when the option list changed.
   */
  _syncAllLevels() {
    if (this._levelsEl === undefined || this._levelsEl === null) {
      return
    }

    const hostDisabled = this._isDisabled()
    const markInvalid = this.hasAttribute("invalid") || this._isUserInvalid() === true
    let invalidMarked = false

    this._placeStateSlots()

    this._levelNodes.forEach((nodes, index) => {
      const cfg = this._levelConfig[index] || {}
      const state = this._levelStates[index] || "idle"
      const value = this._levelValues[index] || ""
      const options = this._levelOptions[index] || []
      const parentMissing = index > 0 && (this._levelValues[index - 1] || "").length === 0

      /* Focus parked on a part that is about to be hidden moves with the level. */
      const active = this.shadowRoot.activeElement
      const hadFocus = active !== null && nodes.wrapper.contains(active) === true

      nodes.loading.hidden = state !== "loading"
      nodes.error.hidden = state !== "error"
      nodes.select.hidden = state !== "idle"

      if (nodes.renderedOptions !== options) {
        this._fillSelect(nodes.select, cfg, options)
        nodes.renderedOptions = options
      }
      nodes.select.value = value
      if (nodes.select.selectedIndex < 0) {
        /* A value that is not (yet) among the options shows the placeholder. */
        nodes.select.selectedIndex = 0
      }
      nodes.select.disabled = hostDisabled === true || parentMissing === true

      if (hadFocus === true && active.closest("[hidden]") !== null) {
        this._focusLevel(nodes, state)
      }

      /* The first incomplete level carries the invalid state. */
      if (markInvalid === true && invalidMarked === false && value.length === 0) {
        nodes.select.setAttribute("aria-invalid", "true")
        invalidMarked = true
      } else {
        nodes.select.removeAttribute("aria-invalid")
      }
    })
    return
  }

  /*
   * Move the level-loading slot into the level that is loading and the
   * level-error slot into the level that failed (see header). A level in
   * that state without the slot (never expected) shows the built-in
   * placeholder / message. A slot left in a level that changed state stays
   * there hidden until another level needs it.
   */
  _placeStateSlots() {
    const loadingIndex = this._levelStates.indexOf("loading")
    const errorIndex = this._levelStates.indexOf("error")

    const loadingNodes = this._levelNodes[loadingIndex]
    if (loadingNodes !== undefined && this._loadingSlot.parentNode !== loadingNodes.loading) {
      loadingNodes.loading.appendChild(this._loadingSlot)
    }

    const errorNodes = this._levelNodes[errorIndex]
    if (errorNodes !== undefined && this._errorSlot.parentNode !== errorNodes.errorMessage) {
      /* The level that held the slot gets its plain message back. */
      const previousHolder = this._errorSlot.parentNode
      errorNodes.errorMessage.replaceChildren(this._errorSlot)
      if (previousHolder !== null) {
        previousHolder.textContent = t("mj.cascadingSelect.loadError")
      }
    }
    return
  }

  /* Put focus on whichever part of a level is showing. */
  _focusLevel(nodes, state) {
    if (state === "loading") {
      nodes.loading.focus()
    } else if (state === "error") {
      nodes.error.querySelector(".level-retry").focus()
    } else if (nodes.select.disabled === false) {
      nodes.select.focus()
    }
    return
  }

  /* Name and disabled state of the role="group" container. */
  _syncGroup() {
    if (this._levelsEl === undefined || this._levelsEl === null) {
      return
    }

    const name = this.getAttribute("label") || this.getAttribute("aria-label") || ""
    if (name.length > 0) {
      this._levelsEl.setAttribute("aria-label", name)
    } else {
      this._levelsEl.removeAttribute("aria-label")
    }

    if (this._isDisabled() === true) {
      this._levelsEl.setAttribute("aria-disabled", "true")
    } else {
      this._levelsEl.removeAttribute("aria-disabled")
    }
    return
  }

  /* ----- event handlers ----- */

  _onLevelChange(event) {
    const select = event.target instanceof Element ? event.target.closest(".level-select") : null
    if (select === null) {
      return
    }

    const index = parseInt(select.dataset.level, 10)
    const newValue = select.value

    this._levelValues[index] = newValue
    this._clearValuesFrom(index + 1)

    this.emit("mj-change", {
      levelIndex: index,
      value: newValue,
      values: this._levelValues.slice()
    })

    /* Work out the options of the levels that depend on this one. */
    this._resolveFrom(index + 1)

    const allFilled = this._levelValues.length > 0 && this._levelValues.every((value) => value.length > 0)
    if (allFilled === true) {
      this.emit("mj-complete", { values: this._levelValues.slice() })
    }
    return
  }

  /* Retry button of a level whose load failed. */
  _onLevelsClick(event) {
    const retry = event.target instanceof Element ? event.target.closest(".level-retry") : null
    if (retry === null) {
      return
    }

    /* _syncAllLevels() moves focus from the retry button to what replaces it. */
    const index = parseInt(retry.dataset.level, 10)
    this._resolveFrom(index)
    return
  }

  /* ----- form participation ----- */

  /*
   * Submit the JSON array under the host name and, for levels configured
   * with a `name`, one entry per level.
   */
  _syncFormValue() {
    const count = this._levelConfig.length
    const json = count > 0 ? JSON.stringify(this._levelValues.slice(0, count)) : ""
    this._setFormValue(json)

    const named = this._levelConfig.some((cfg) => {
      return cfg !== null && cfg !== undefined && typeof cfg.name === "string" && cfg.name.length > 0
    })

    if (named === true && this._internals !== null) {
      const data = new FormData()
      const hostName = this.getAttribute("name") || ""
      if (hostName.length > 0) {
        data.append(hostName, json)
      }
      this._levelConfig.forEach((cfg, index) => {
        if (cfg !== null && cfg !== undefined && typeof cfg.name === "string" && cfg.name.length > 0) {
          data.append(cfg.name, this._levelValues[index] || "")
        }
      })
      this._internals.setFormValue(data, json)
    }
    return
  }

  _customValidity() {
    const required = this.hasAttribute("required")
    if (required === true) {
      const incomplete = this._levelValues.some((v) => v.length === 0)
      if (incomplete === true) {
        return t("mj.cascadingSelect.levelsRequired")
      }
    }
    return ""
  }

  /*
   * The validation bubble points at the first level still missing a value.
   * A hidden or disabled select cannot anchor it, so the first usable select
   * is the fallback; null lets the base class report without an anchor.
   */
  /*
   * FormControlMixin hooks: a failed validation (an mj-form submit) marks the
   * control invalid, as the `invalid` attribute does, until it is valid again.
   */
  onInvalid(message) {
    if (this._levelsEl !== undefined && this._levelsEl !== null) {
      this._syncAllLevels()
    }
    return
  }

  onValidityRestored() {
    if (this._levelsEl !== undefined && this._levelsEl !== null) {
      this._syncAllLevels()
    }
    return
  }

  _validationAnchor() {
    let anchor = null
    let fallback = null

    for (let index = 0; index < this._levelNodes.length; index = index + 1) {
      const select = this._levelNodes[index].select
      const usable = select.hidden === false && select.disabled === false
      if (usable === true) {
        if (fallback === null) {
          fallback = select
        }
        if ((this._levelValues[index] || "").length === 0) {
          anchor = select
          break
        }
      }
    }

    if (anchor === null) {
      anchor = fallback
    }
    return anchor
  }

  /* Reset goes back to the default values given by the `value` attribute. */
  onFormReset(initial) {
    this._applyValues(parseValueList(initial))
    return
  }

  onFormRestore(state) {
    this._applyValues(parseValueList(state))
    return
  }

  /* An ancestor <fieldset disabled> was switched on or off. */
  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    this._syncAllLevels()
    this._syncGroup()
    return
  }
}
