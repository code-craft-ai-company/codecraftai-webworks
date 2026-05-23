/*
 * mjcascadingselect.js
 *
 * <mj-cascading-select> — ordered chain of dependent selects where each
 * level's options depend on the previous level's selection.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { announce } from "../core/announcer.js";

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
  color: var(--mj-color-danger);
  font-size: var(--mj-font-size-sm);
  padding: var(--mj-space-1) 0;
}
`;

export class MjCascadingSelect extends FormControlMixin(MjElement) {
  static tagName = "mj-cascading-select";
  static styles = STYLES;
  static watched = ["disabled", "required", "orientation", "size"];

  constructor() {
    super()
    this._initFormControl()
    this._levelValues = []
    this._levelStates = []   /* "idle" | "loading" | "error" */
    this._levelOptions = []  /* arrays of {value, label} per level */
    this._abortControllers = []
    this._levelConfig = []
  }

  render() {
    const markup = `<div class="levels" part="levels"></div>`
    return markup
  }

  afterRender() {
    this._levelsEl = this.$(".levels")
    this._renderLevels()
    return
  }

  /* ----- public API: set levels config ----- */

  get levels() {
    return this._levelConfig
  }

  set levels(configs) {
    this._levelConfig = configs || []
    this._levelValues = new Array(this._levelConfig.length).fill("")
    this._levelStates = new Array(this._levelConfig.length).fill("idle")
    this._levelOptions = this._levelConfig.map((cfg) => cfg.options || [])
    this._renderLevels()
    return
  }

  get values() {
    return this._levelValues.slice()
  }

  set values(vals) {
    this._levelValues = vals.slice()
    this._renderLevels()
    return
  }

  /* ----- rendering ----- */

  _renderLevels() {
    if (this._levelsEl === undefined) {
      return
    }

    if (this._levelConfig.length === 0) {
      this._levelsEl.innerHTML = ""
      return
    }

    let html = ""
    this._levelConfig.forEach((cfg, idx) => {
      const state = this._levelStates[idx] || "idle"
      const value = this._levelValues[idx] || ""
      const disabled = this.hasAttribute("disabled") || (idx > 0 && (this._levelValues[idx - 1] || "").length === 0)
      const labelId = nextId("mj-cs-label")

      let controlHtml = ""
      if (state === "loading") {
        controlHtml = `<div class="level-loading" part="level-loading" aria-busy="true"><slot name="level-loading"></slot></div>`
      } else if (state === "error") {
        controlHtml = `<div class="level-error" part="level-error" role="alert"><slot name="level-error">Failed to load options</slot></div>`
      } else {
        const options = this._levelOptions[idx] || []
        const ph = cfg.placeholder || "Select..."
        let optHtml = `<option value="">${ph}</option>`
        options.forEach((opt) => {
          const selected = opt.value === value ? " selected" : ""
          optHtml += `<option value="${opt.value}"${selected}>${opt.label}</option>`
        })
        controlHtml = `<select
          class="level-select"
          part="level"
          data-level="${idx}"
          aria-labelledby="${labelId}"
          ${disabled === true ? "disabled" : ""}
        >${optHtml}</select>`
      }

      html += `<div class="level" part="level">
        <span class="level-label" part="level-label" id="${labelId}">${cfg.label || ""}</span>
        ${controlHtml}
      </div>`
    })
    this._levelsEl.innerHTML = html

    const selects = this._levelsEl.querySelectorAll(".level-select")
    selects.forEach((sel) => {
      this.listen(sel, "change", this._onLevelChange.bind(this))
    })
    return
  }

  _onLevelChange(event) {
    const idx = parseInt(event.target.dataset.level, 10)
    const newValue = event.target.value

    const previousValues = this._levelValues.slice()
    this._levelValues[idx] = newValue

    /* Reset all downstream levels */
    for (let i = idx + 1; i < this._levelValues.length; i = i + 1) {
      this._levelValues[i] = ""
      this._levelOptions[i] = []
      this._levelStates[i] = "idle"

      if (this._abortControllers[i] !== undefined) {
        this._abortControllers[i].abort()
        this._abortControllers[i] = undefined
      }
    }

    this.emit("mj-change", {
      levelIndex: idx,
      value: newValue,
      values: this._levelValues.slice()
    })

    /* Trigger async load for next level if src/dataSource present */
    const nextIdx = idx + 1
    if (nextIdx < this._levelConfig.length && newValue.length > 0) {
      const nextCfg = this._levelConfig[nextIdx]
      if (nextCfg.src !== undefined && nextCfg.src.length > 0) {
        this._loadLevelOptions(nextIdx, nextCfg.src.replace("{parentValue}", encodeURIComponent(newValue)))
      } else if (nextCfg.dataSource !== undefined) {
        this._loadFromDataSource(nextIdx, newValue, nextCfg.dataSource)
      }
    }

    this._syncFormValue()
    this._renderLevels()

    const allFilled = this._levelValues.every((v) => v.length > 0)
    if (allFilled === true) {
      this.emit("mj-complete", { values: this._levelValues.slice() })
    }
    return
  }

  _loadLevelOptions(levelIdx, url) {
    this._levelStates[levelIdx] = "loading"
    this._renderLevels()
    this.emit("mj-level-load-start", { levelIndex: levelIdx, parentValue: this._levelValues[levelIdx - 1] })

    const controller = new AbortController()
    this._abortControllers[levelIdx] = controller

    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (res.ok === false) {
          throw new Error(`HTTP ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        this._levelOptions[levelIdx] = data
        this._levelStates[levelIdx] = "idle"
        this.emit("mj-level-load-end", { levelIndex: levelIdx, options: data })
        this._renderLevels()
      })
      .catch((err) => {
        if (err.name === "AbortError") {
          return
        }
        this._levelStates[levelIdx] = "error"
        this.emit("mj-level-error", { levelIndex: levelIdx, error: err })
        announce(`Failed to load options`, "assertive")
        this._renderLevels()
      })
    return
  }

  _loadFromDataSource(levelIdx, parentValue, dataSource) {
    this._levelStates[levelIdx] = "loading"
    this._renderLevels()
    this.emit("mj-level-load-start", { levelIndex: levelIdx, parentValue: parentValue })

    const promise = dataSource.query({ filter: parentValue })
    promise
      .then((result) => {
        this._levelOptions[levelIdx] = result.items || result
        this._levelStates[levelIdx] = "idle"
        this.emit("mj-level-load-end", { levelIndex: levelIdx, options: this._levelOptions[levelIdx] })
        this._renderLevels()
      })
      .catch((err) => {
        this._levelStates[levelIdx] = "error"
        this.emit("mj-level-error", { levelIndex: levelIdx, error: err })
        this._renderLevels()
      })
    return
  }

  _syncFormValue() {
    const val = JSON.stringify(this._levelValues)
    this._setFormValue(val)
    return
  }

  _customValidity() {
    const required = this.hasAttribute("required")
    if (required === true) {
      const incomplete = this._levelValues.some((v) => v.length === 0)
      if (incomplete === true) {
        return "All levels must be selected."
      }
    }
    return ""
  }

  onFormReset() {
    this._levelValues = new Array(this._levelConfig.length).fill("")
    this._renderLevels()
    return
  }
}
