/*
 * mjrowselector.js
 *
 * <mj-row-selector> -- a checkbox-based row selector that pairs
 * with DataTable / List / treegrid hosts. Two operating modes:
 *
 *   mode="row" (default) -- selects one row. Carries a `value`
 *   that identifies the row in the host's selection model.
 *
 *   mode="all" -- the "select all" header companion. Supports
 *   `indeterminate` so the host can express the "some but not
 *   all rows are selected" state. Activation clears the
 *   indeterminate state and forces selected=true; activating
 *   again clears selected.
 *
 * Emits `mj-row-select-change` with the new
 * `{ selected, indeterminate, mode, value }` on every transition.
 *
 * Form-associated via ElementInternals so a select-all column
 * inside a `<form>` reports its checkbox state on submit and
 * participates in validity. Hosts that drive selection at the
 * dataset level should ignore the form value and consume the
 * events instead.
 *
 * Theming: every visual value is a `--mj-row-selector-*` token
 * with library fallbacks. Tokens override per-instance.
 *
 * Docking + anchoring: inherited from MjElement.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
  gap: var(--mj-space-2);
  font: inherit;
  color: var(--mj-row-selector-color, var(--mj-text));
}

:host([disabled]) {
  opacity: 0.55;
  pointer-events: none;
}

.wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-row-selector-height, var(--mj-target-min));
  padding: var(--mj-row-selector-padding, var(--mj-space-1));
  border-radius: var(--mj-row-selector-border-radius, var(--mj-radius-sm));
  cursor: pointer;
  user-select: none;
}

.wrap:hover {
  background: var(--mj-row-selector-bg-hover, var(--mj-bg-muted));
}

input[type="checkbox"] {
  width: var(--mj-row-selector-size, 1rem);
  height: var(--mj-row-selector-size, 1rem);
  margin: 0;
  accent-color: var(--mj-row-selector-accent, var(--mj-accent));
  cursor: inherit;
}

input[type="checkbox"]:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-row-selector-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

.label {
  font: inherit;
  font-size: var(--mj-row-selector-label-font-size, inherit);
  line-height: 1.2;
}

.label[hidden] { display: none; }

.count {
  font-variant-numeric: tabular-nums;
  color: var(--mj-row-selector-count-color, var(--mj-text-muted));
}

.count[hidden] { display: none; }
`;

export class MjRowSelector extends MjElement {
    static tagName = "mj-row-selector";
    static styles = STYLES;
    static watched = [
        "mode",
        "selected",
        "indeterminate",
        "disabled",
        "value",
        "name",
        "label",
        "count",
    ];
    static formAssociated = true;

    constructor() {
        super();
        this._wrap = null;
        this._checkbox = null;
        this._label_el = null;
        this._count_el = null;
        this._internals = null;
        if (typeof this.attachInternals === "function") {
            this._internals = this.attachInternals();
        }
    }

    render() {
        const markup = `
            <label class="wrap" part="wrap">
                <input type="checkbox" part="checkbox">
                <span class="label" part="label"><slot></slot></span>
                <span class="count" part="count" hidden></span>
            </label>
        `;
        return markup;
    }

    afterRender() {
        this._wrap = this.$(".wrap");
        this._checkbox = this.$("input[type=checkbox]");
        this._label_el = this.$(".label");
        this._count_el = this.$(".count");
        if (this._checkbox !== null) {
            this._checkbox.addEventListener("change", (event) => {
                this._on_native_change(event);
            });
            this._checkbox.addEventListener("click", (event) => {
                event.stopPropagation();
            });
        }
        this._sync();
        return;
    }

    onAttributeChanged(name, oldValue, newValue) {
        if (this._checkbox === null) {
            return;
        }
        this._sync();
        return;
    }

    _on_native_change(event) {
        const next_selected = this._checkbox.checked === true;
        const previously_indeterminate = this.hasAttribute("indeterminate");
        // Activation clears any indeterminate state regardless of mode.
        if (previously_indeterminate === true) {
            this.removeAttribute("indeterminate");
        }
        if (next_selected === true) {
            this.setAttribute("selected", "");
        } else {
            this.removeAttribute("selected");
        }
        this._sync();
        this.emit(
            "mj-row-select-change",
            {
                selected: next_selected,
                indeterminate: false,
                mode: this.mode,
                value: this.value,
            },
            { bubbles: true, composed: true },
        );
        return;
    }

    _sync() {
        const selected = this.hasAttribute("selected");
        const indeterminate = this.hasAttribute("indeterminate");
        if (this._checkbox !== null) {
            this._checkbox.checked = selected;
            this._checkbox.indeterminate = indeterminate;
            if (this.hasAttribute("disabled") === true) {
                this._checkbox.setAttribute("disabled", "");
            } else {
                this._checkbox.removeAttribute("disabled");
            }
            this._checkbox.setAttribute("aria-label", this._aria_label());
        }
        const count_attr = this.getAttribute("count");
        if (this._count_el !== null) {
            if (this.mode === "all" && count_attr !== null && count_attr.length > 0) {
                this._count_el.hidden = false;
                this._count_el.textContent = "(" + count_attr + ")";
            } else {
                this._count_el.hidden = true;
                this._count_el.textContent = "";
            }
        }
        if (this._label_el !== null) {
            const has_slotted = this._has_slotted_label();
            this._label_el.hidden = has_slotted === false;
        }
        if (this._internals !== null) {
            const form_value = selected === true ? (this.value || "on") : null;
            this._internals.setFormValue(form_value);
        }
        return;
    }

    _has_slotted_label() {
        const slot = this.$("slot");
        if (slot === null) {
            return false;
        }
        const assigned = slot.assignedNodes({ flatten: true });
        for (const node of assigned) {
            if (node.nodeType === Node.ELEMENT_NODE) {
                return true;
            }
            if (
                node.nodeType === Node.TEXT_NODE &&
                node.textContent.trim().length > 0
            ) {
                return true;
            }
        }
        return false;
    }

    _aria_label() {
        const explicit = this.getAttribute("label");
        if (explicit !== null && explicit.length > 0) {
            return explicit;
        }
        if (this.mode === "all") {
            const count = this.getAttribute("count") || "";
            const base = "Select all rows";
            return count.length > 0 ? base + " (" + count + ")" : base;
        }
        const value = this.value;
        return value.length > 0 ? "Select row " + value : "Select row";
    }

    get mode() {
        const raw = this.getAttribute("mode") || "row";
        return raw === "all" ? "all" : "row";
    }

    set mode(value) {
        if (value === "all" || value === "row") {
            this.setAttribute("mode", value);
        }
        return;
    }

    get selected() {
        return this.hasAttribute("selected");
    }

    set selected(value) {
        if (value === true) {
            this.setAttribute("selected", "");
        } else {
            this.removeAttribute("selected");
        }
        return;
    }

    get indeterminate() {
        return this.hasAttribute("indeterminate");
    }

    set indeterminate(value) {
        if (value === true) {
            this.setAttribute("indeterminate", "");
        } else {
            this.removeAttribute("indeterminate");
        }
        return;
    }

    get disabled() {
        return this.hasAttribute("disabled");
    }

    set disabled(value) {
        if (value === true) {
            this.setAttribute("disabled", "");
        } else {
            this.removeAttribute("disabled");
        }
        return;
    }

    get value() {
        const rtnval = this.getAttribute("value") || "";
        return rtnval;
    }

    set value(value) {
        this.setAttribute("value", String(value));
        return;
    }

    get name() {
        const rtnval = this.getAttribute("name") || "";
        return rtnval;
    }

    set name(value) {
        this.setAttribute("name", String(value));
        return;
    }
}
