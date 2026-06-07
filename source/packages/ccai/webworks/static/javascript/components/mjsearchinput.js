/*
 * mjsearchinput.js
 *
 * <mj-search-input> -- search field with leading icon, clear button,
 * optional suggestions popup, and submit-on-Enter semantics.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.search-wrap {
  position: relative;
}

.field {
  display: flex;
  align-items: center;
  min-height: var(--mj-control-height-md);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-pill);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
}
.field:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.search-icon {
  display: flex;
  align-items: center;
  padding: 0 var(--mj-space-3);
  color: var(--mj-text-muted);
  flex-shrink: 0;
  pointer-events: none;
}
.search-icon svg { width: 1rem; height: 1rem; }

input {
  flex: 1;
  min-width: 0;
  padding: 0 var(--mj-space-2);
  font: inherit;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
}
input::-webkit-search-cancel-button { display: none; }
input::placeholder { color: var(--mj-text-muted); }

.clear-btn, .submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  margin-inline-end: var(--mj-space-1);
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-circle);
  cursor: pointer;
  color: var(--mj-text-muted);
  flex-shrink: 0;
}
.clear-btn:hover, .submit-btn:hover { color: var(--mj-text); background: var(--mj-bg-muted); }
.clear-btn:focus-visible, .submit-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.clear-btn[hidden] { display: none; }
.submit-btn[hidden] { display: none; }

.popup {
  position: absolute;
  top: calc(100% + var(--mj-space-1));
  inset-inline-start: 0;
  inset-inline-end: 0;
  background: var(--mj-surface-raised);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  box-shadow: var(--mj-elevation-2);
  max-height: 300px;
  overflow-y: auto;
  z-index: var(--mj-layer-popover);
}
.popup[hidden] { display: none; }

.option {
  padding: var(--mj-space-2) var(--mj-space-3);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.option:hover, .option[data-active] { background: var(--mj-bg-muted); }

.loading-msg {
  padding: var(--mj-space-3);
  color: var(--mj-text-muted);
  font-size: var(--mj-font-size-sm);
}

.help {
  margin-top: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text-muted);
}
.help:empty { display: none; }

:host([disabled]) .field { opacity: 0.55; pointer-events: none; }
`;

export class MjSearchInput extends FormControlMixin(MjElement) {
  static tagName = "mj-search-input";
  static styles = STYLES;
  static watched = [
    "value", "placeholder", "label", "help-text", "disabled", "readonly",
    "required", "show-submit-button", "loading", "debounce", "min-chars", "no-clear-button"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._suggestions = [];
    this._activeIndex = -1;
    this._debounceTimer = null;
    this._popupId = nextId("mjsi-popup");
    this._helpId = nextId("mjsi-help");
    this._prevValue = "";
  }

  render() {
    const label = this.getAttribute("label") || "Search";
    const placeholder = this.getAttribute("placeholder") || "Search";
    const markup = `
      <div role="search" aria-label="${label}" part="search">
        <div class="search-wrap">
          <div class="field" part="field">
            <span class="search-icon" part="search-icon" aria-hidden="true">
              <slot name="search-icon">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                  <circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5l3 3"/>
                </svg>
              </slot>
            </span>
            <input
              part="input"
              type="search"
              role="searchbox"
              placeholder="${placeholder}"
              autocomplete="off"
              aria-controls="${this._popupId}"
              aria-expanded="false"
              aria-autocomplete="list"
            />
            <button class="clear-btn" part="clear-button" type="button" aria-label="Clear search" hidden></button>
            <button class="submit-btn" part="submit-button" type="submit" hidden>
              <slot name="submit-icon">&#x2192;</slot>
            </button>
          </div>
          <div class="popup" part="popup" id="${this._popupId}" role="listbox" hidden></div>
        </div>
        <span class="help" part="help" id="${this._helpId}"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._input = this.$("input");
    this._clearBtn = this.$(".clear-btn");
    this._submitBtn = this.$(".submit-btn");
    this._popup = this.$(".popup");
    this._helpEl = this.$(".help");

    this._syncAll();

    this.listen(this._input, "input", this._onInput.bind(this));
    this.listen(this._input, "keydown", this._onKeydown.bind(this));
    this.listen(this._clearBtn, "click", this._onClear.bind(this));
    this.listen(this._submitBtn, "click", this._onSubmit.bind(this));
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
    const label = this.getAttribute("label") || "Search";
    const placeholder = this.getAttribute("placeholder") || "Search";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const showSubmit = this.hasAttribute("show-submit-button");
    const noClear = this.hasAttribute("no-clear-button");

    this._input.placeholder = placeholder;
    this._input.disabled = disabled;
    this._input.readOnly = readonly;
    this._helpEl.textContent = helpText;

    this._submitBtn.hidden = !showSubmit;
    if (noClear) {
      this._clearBtn.hidden = true;
    }

    const searchDiv = this.$("[role='search']");
    if (searchDiv !== null) {
      searchDiv.setAttribute("aria-label", label);
    }
    return;
  }

  _onInput(event) {
    const val = this._input.value;
    this._setFormValue(val);
    this._prevValue = val;

    const noClear = this.hasAttribute("no-clear-button");
    if (!noClear) {
      this._clearBtn.hidden = val.length === 0;
    }

    this.emit("mj-input", { value: val });

    if (this._debounceTimer !== null) {
      clearTimeout(this._debounceTimer);
    }
    const debounce = parseInt(this.getAttribute("debounce") || "300", 10);
    const minChars = parseInt(this.getAttribute("min-chars") || "1", 10);

    this._debounceTimer = setTimeout(() => {
      if (val.length >= minChars) {
        this.emit("mj-query-change", { value: val });
      }
    }, debounce);
    return;
  }

  _onKeydown(event) {
    const key = event.key;

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
    if (key === "Enter") {
      if (this._activeIndex >= 0 && this._activeIndex < this._suggestions.length) {
        event.preventDefault();
        this._selectSuggestion(this._suggestions[this._activeIndex]);
      } else {
        const notCanceled = this.emit("mj-search", { value: this._input.value }, { cancelable: true });
        if (notCanceled) {
          const form = this.form;
          if (form !== null) {
            form.requestSubmit();
          }
        }
      }
      return;
    }
    if (key === "Escape") {
      this._closePopup();
      return;
    }
    return;
  }

  _onClear(event) {
    const prev = this._input.value;
    this._input.value = "";
    this._setFormValue("");
    this._clearBtn.hidden = true;
    this._closePopup();
    this.emit("mj-clear", { previousValue: prev });
    this._input.focus();
    return;
  }

  _onSubmit(event) {
    const notCanceled = this.emit("mj-search", { value: this._input.value }, { cancelable: true });
    if (notCanceled) {
      const form = this.form;
      if (form !== null) {
        form.requestSubmit();
      }
    }
    return;
  }

  _onOutsideClick(event) {
    if (!this.contains(event.target)) {
      this._closePopup();
    }
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
    this._input.value = suggestion.value;
    this._setFormValue(suggestion.value);
    this._closePopup();
    this.emit("mj-suggestion-select", { suggestion });
    this.emit("mj-search", { value: suggestion.value });
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
    const loading = this.hasAttribute("loading");
    this._popup.innerHTML = "";

    if (loading) {
      const msg = document.createElement("div");
      msg.className = "loading-msg";
      msg.setAttribute("role", "status");
      msg.textContent = "Loading suggestions…";
      this._popup.appendChild(msg);
      this._popup.hidden = false;
      this._input.setAttribute("aria-expanded", "true");
      return;
    }

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

  get suggestions() {
    return this._suggestions;
  }

  set suggestions(arr) {
    this._suggestions = Array.isArray(arr) ? arr : [];
    this._activeIndex = -1;
    this._renderPopup();
    return;
  }

  get loading() {
    return this.hasAttribute("loading");
  }

  set loading(val) {
    this.reflectBoolean("loading", val === true);
    if (this._popup !== undefined) {
      this._renderPopup();
    }
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._input === undefined) {
      return;
    }
    if (name === "loading") {
      this._renderPopup();
    }
    this._syncAll();
    return;
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus();
    }
    return;
  }
}
