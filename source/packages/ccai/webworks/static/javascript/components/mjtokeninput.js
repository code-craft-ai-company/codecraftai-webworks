/*
 * mjtokeninput.js
 *
 * <mj-token-input> -- multi-value chip/tag input with optional suggestion
 * popup, delimiter-based token commit, and form participation.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

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

.container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--mj-space-1);
  min-height: var(--mj-control-height-md);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  cursor: text;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.container:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.container[data-invalid] { border-color: var(--mj-color-danger); }

.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  padding: var(--mj-space-1) var(--mj-space-2);
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  max-width: 200px;
}
.chip[aria-selected="true"] {
  background: var(--mj-accent);
  color: var(--mj-text-on-accent);
}

.chip-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  border-radius: var(--mj-radius-circle);
  font-size: 0.75rem;
  line-height: 1;
  flex-shrink: 0;
}
.chip-remove:hover { background: rgba(0,0,0,0.15); }
.chip-remove:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }

.chip-remove[hidden] { display: none; }

input {
  flex: 1;
  min-width: 120px;
  height: 1.75rem;
  padding: 0 var(--mj-space-1);
  font: inherit;
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
}
input[hidden] { display: none; }
input::placeholder { color: var(--mj-text-muted); }

.popup {
  position: absolute;
  inset-inline-start: 0;
  inset-inline-end: 0;
  top: calc(100% + 4px);
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  max-height: 250px;
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
}
.popup[hidden] { display: none; }

.option {
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  font-size: var(--mj-font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.option:hover, .option[data-active] { background: var(--mj-bg-muted); }

.container-wrap { position: relative; }

.max-msg {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  padding: var(--mj-space-1);
}
.max-msg[hidden] { display: none; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

.announce { position: absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }

:host([disabled]) .container { opacity: 0.55; pointer-events: none; }
`;

export class MjTokenInput extends FormControlMixin(MjElement) {
  static tagName = "mj-token-input";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message",
    "delimiters", "max-tokens", "allow-duplicates", "required",
    "disabled", "readonly", "trim", "loading", "debounce", "min-chars"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._tokens = [];
    this._suggestions = [];
    this._activeIndex = -1;
    this._selectedChipIndex = -1;
    this._debounceTimer = null;
    this._validateToken = null;
    this._groupId = nextId("mjti-group");
    this._popupId = nextId("mjti-popup");
    this._helpId = nextId("mjti-help");
    this._errorId = nextId("mjti-error");
    this._announceId = nextId("mjti-announce");
  }

  render() {
    const markup = `
      <label class="label" part="label"></label>
      <div class="container-wrap">
        <div class="container" part="container" role="group" id="${this._groupId}">
          <input
            part="input"
            type="text"
            aria-label="Add tag"
            aria-controls="${this._popupId}"
            aria-expanded="false"
            aria-autocomplete="list"
          />
          <span class="max-msg" hidden></span>
        </div>
        <div class="popup" part="popup" id="${this._popupId}" role="listbox" hidden></div>
      </div>
      <span class="announce" id="${this._announceId}" aria-live="polite" role="status"></span>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._container = this.$(".container");
    this._input = this.$("input");
    this._popup = this.$(".popup");
    this._maxMsg = this.$(".max-msg");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._announceEl = this.$(".announce");

    this._syncAll();

    this.listen(this._input, "keydown", this._onKeydown.bind(this));
    this.listen(this._input, "input", this._onInput.bind(this));
    this.listen(this._container, "click", this._onContainerClick.bind(this));
    this.listen(document, "click", this._onOutsideClick.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._input === undefined) {
      return;
    }
    this._syncAll();
    return;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const placeholder = this.getAttribute("placeholder") || "";
    const helpText = this.getAttribute("help-text") || "";
    const readonly = this.hasAttribute("readonly");
    const maxTokens = this.getAttribute("max-tokens");

    this._labelEl.textContent = label;
    this._input.placeholder = placeholder;
    this._helpEl.textContent = helpText;

    const container = this.$("[role='group']");
    if (container !== null) {
      container.setAttribute("aria-label", label || "Token input");
    }

    const atMax = maxTokens !== null && this._tokens.length >= parseInt(maxTokens, 10);
    this._input.hidden = atMax || readonly;
    this._maxMsg.hidden = !atMax;
    if (atMax) {
      this._maxMsg.textContent = `Maximum ${maxTokens} tags reached`;
    }
    return;
  }

  _onContainerClick(event) {
    if (event.target === this._container) {
      this._input.focus();
    }
    return;
  }

  _onInput(event) {
    const val = this._input.value;
    this.emit("mj-input", { value: val });

    const delimiters = this.getAttribute("delimiters") || ",\n";
    for (let i = 0; i < delimiters.length; i = i + 1) {
      if (val.includes(delimiters[i])) {
        const parts = val.split(delimiters[i]);
        for (let j = 0; j < parts.length - 1; j = j + 1) {
          this._tryAddToken(parts[j]);
        }
        this._input.value = parts[parts.length - 1];
        return;
      }
    }

    if (this._debounceTimer !== null) {
      clearTimeout(this._debounceTimer);
    }
    const debounce = parseInt(this.getAttribute("debounce") || "300", 10);
    const minChars = parseInt(this.getAttribute("min-chars") || "1", 10);
    this._debounceTimer = setTimeout(() => {
      if (this._input.value.length >= minChars) {
        this.emit("mj-query-change", { value: this._input.value });
      }
    }, debounce);
    return;
  }

  _onKeydown(event) {
    const key = event.key;
    const val = this._input.value;

    if (key === "Enter") {
      event.preventDefault();
      if (this._activeIndex >= 0 && this._activeIndex < this._suggestions.length) {
        this._selectSuggestion(this._suggestions[this._activeIndex]);
      } else if (val.length > 0) {
        this._tryAddToken(val);
        this._input.value = "";
      }
      return;
    }
    if (key === "Tab" && val.length > 0) {
      this._tryAddToken(val);
      this._input.value = "";
      return;
    }
    if (key === "Backspace" && val.length === 0) {
      if (this._selectedChipIndex >= 0) {
        this._removeTokenAt(this._selectedChipIndex);
        this._selectedChipIndex = -1;
      } else if (this._tokens.length > 0) {
        this._selectedChipIndex = this._tokens.length - 1;
        this._renderTokens();
      }
      return;
    }
    if (key === "ArrowLeft" && val.length === 0 && this._tokens.length > 0) {
      this._selectedChipIndex = this._tokens.length - 1;
      this._renderTokens();
      return;
    }
    if (key === "ArrowDown") {
      event.preventDefault();
      this._moveActive(1);
      return;
    }
    if (key === "ArrowUp") {
      event.preventDefault();
      this._moveActive(-1);
      return;
    }
    if (key === "Escape") {
      this._closePopup();
      this._selectedChipIndex = -1;
      this._renderTokens();
      return;
    }
    if (key !== "Backspace" && key !== "ArrowLeft" && key !== "ArrowRight") {
      this._selectedChipIndex = -1;
    }
    return;
  }

  _tryAddToken(rawVal) {
    const trimFlag = this.getAttribute("trim") !== "false";
    const val = trimFlag ? rawVal.trim() : rawVal;
    if (val.length === 0) {
      return;
    }

    const maxTokens = this.getAttribute("max-tokens");
    if (maxTokens !== null && this._tokens.length >= parseInt(maxTokens, 10)) {
      return;
    }

    const allowDups = this.hasAttribute("allow-duplicates");
    if (!allowDups && this._tokens.includes(val)) {
      this._announceEl.textContent = `${val} is already added`;
      return;
    }

    if (this._validateToken !== null) {
      const result = this._validateToken(val);
      if (result !== true) {
        const msg = typeof result === "string" ? result : "Invalid value";
        this._errorEl.textContent = msg;
        this._errorEl.setAttribute("data-visible", "");
        this.emit("mj-invalid", { validationMessage: msg });
        return;
      }
    }

    const notCanceled = this.emit("mj-token-add", { value: val, tokens: [...this._tokens] }, { cancelable: true });
    if (!notCanceled) {
      return;
    }

    this._tokens.push(val);
    this._refreshFormValue();
    this._renderTokens();
    this._syncAll();
    this.emit("mj-change", { tokens: [...this._tokens] });
    this._announceEl.textContent = `${val} added`;
    return;
  }

  _removeTokenAt(index) {
    const val = this._tokens[index];
    const notCanceled = this.emit("mj-token-remove", { value: val, tokens: [...this._tokens] }, { cancelable: true });
    if (!notCanceled) {
      return;
    }
    this._tokens.splice(index, 1);
    this._refreshFormValue();
    this._renderTokens();
    this._syncAll();
    this.emit("mj-change", { tokens: [...this._tokens] });
    this._announceEl.textContent = `${val} removed`;
    return;
  }

  _refreshFormValue() {
    if (this._internals === null) {
      return;
    }
    const fd = new FormData();
    const name = this.getAttribute("name") || "";
    for (let i = 0; i < this._tokens.length; i = i + 1) {
      fd.append(name, this._tokens[i]);
    }
    this._internals.setFormValue(fd);
    this._refreshValidity();
    return;
  }

  _renderTokens() {
    const readonly = this.hasAttribute("readonly");
    const chips = this._container.querySelectorAll(".chip");
    chips.forEach(c => c.remove());

    const insertBefore = this._input;
    this._tokens.forEach((token, idx) => {
      const chip = document.createElement("div");
      chip.className = "chip";
      chip.setAttribute("part", "token");
      chip.setAttribute("role", "option");
      chip.setAttribute("aria-selected", idx === this._selectedChipIndex ? "true" : "false");
      chip.title = token;

      const lbl = document.createElement("span");
      lbl.className = "chip-label";
      lbl.setAttribute("part", "token-label");
      lbl.textContent = token;

      const removeBtn = document.createElement("button");
      removeBtn.className = "chip-remove";
      removeBtn.setAttribute("part", "token-remove");
      removeBtn.setAttribute("type", "button");
      removeBtn.setAttribute("aria-label", `Remove ${token}`);
      removeBtn.textContent = "×";
      removeBtn.hidden = readonly;
      removeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._removeTokenAt(idx);
      });

      chip.appendChild(lbl);
      chip.appendChild(removeBtn);
      this._container.insertBefore(chip, insertBefore);
    });
    return;
  }

  _moveActive(dir) {
    const count = this._suggestions.length;
    if (count === 0) {
      return;
    }
    this._activeIndex = this._activeIndex + dir;
    if (this._activeIndex < 0) {
      this._activeIndex = count - 1;
    }
    if (this._activeIndex >= count) {
      this._activeIndex = 0;
    }
    this._renderPopup();
    return;
  }

  _selectSuggestion(suggestion) {
    this._tryAddToken(suggestion.value);
    this._input.value = "";
    this._closePopup();
    this.emit("mj-suggestion-select", { suggestion });
    this._input.focus();
    return;
  }

  _closePopup() {
    this._popup.hidden = true;
    this._input.setAttribute("aria-expanded", "false");
    this._activeIndex = -1;
    return;
  }

  _renderPopup() {
    this._popup.innerHTML = "";
    if (this._suggestions.length === 0) {
      this._closePopup();
      return;
    }
    this._suggestions.forEach((suggestion, idx) => {
      const opt = document.createElement("div");
      opt.className = "option";
      opt.setAttribute("role", "option");
      opt.setAttribute("id", `${this._popupId}-opt-${idx}`);
      opt.textContent = suggestion.label || suggestion.value;
      if (idx === this._activeIndex) {
        opt.setAttribute("data-active", "");
        this._input.setAttribute("aria-activedescendant", opt.id);
      }
      opt.addEventListener("click", () => this._selectSuggestion(suggestion));
      this._popup.appendChild(opt);
    });
    this._popup.hidden = false;
    this._input.setAttribute("aria-expanded", "true");
    return;
  }

  _onOutsideClick(event) {
    if (!this.contains(event.target)) {
      this._closePopup();
    }
    return;
  }

  _runValidation() {
    this._refreshValidity();
    const msg = this.validationMessage;
    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._container.setAttribute("data-invalid", "");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._container.removeAttribute("data-invalid");
    }
    return;
  }

  _customValidity() {
    const required = this.hasAttribute("required");
    if (required && this._tokens.length === 0) {
      return "At least one tag is required.";
    }
    return "";
  }

  onFormReset(initial) {
    const initVal = initial.length > 0 ? initial.split(",") : [];
    this._tokens = initVal.map(v => v.trim()).filter(v => v.length > 0);
    this._refreshFormValue();
    if (this._container !== undefined) {
      this._renderTokens();
      this._syncAll();
    }
    return;
  }

  get tokens() {
    return [...this._tokens];
  }

  set tokens(arr) {
    this._tokens = Array.isArray(arr) ? [...arr] : [];
    this._refreshFormValue();
    if (this._container !== undefined) {
      this._renderTokens();
      this._syncAll();
    }
    return;
  }

  get suggestions() {
    return this._suggestions;
  }

  set suggestions(arr) {
    this._suggestions = Array.isArray(arr) ? arr : [];
    this._activeIndex = -1;
    if (this._popup !== undefined) {
      this._renderPopup();
    }
    return;
  }

  get validateToken() {
    return this._validateToken;
  }

  set validateToken(fn) {
    this._validateToken = typeof fn === "function" ? fn : null;
    return;
  }

  checkValidity() {
    this._refreshValidity();
    const valid = this._internals !== null ? this._internals.checkValidity() : true;
    return valid;
  }

  reportValidity() {
    this._runValidation();
    const valid = this._internals !== null ? this._internals.reportValidity() : true;
    return valid;
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus();
    }
    return;
  }
}
