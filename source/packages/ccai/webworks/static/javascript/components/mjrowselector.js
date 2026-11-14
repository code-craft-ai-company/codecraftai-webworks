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
 *   all rows are selected" state.
 *
 * In either mode, activation from the indeterminate state clears
 * it and forces selected=true (also when `selected` was set
 * together with `indeterminate`); activating again clears
 * selected.
 *
 * Emits `mj-row-select-change` with the new
 * `{ selected, indeterminate, mode, value, shiftKey }` on every
 * transition. A click on the control never reaches the row it is
 * placed in, also while the control is disabled.
 *
 * Form-associated via ElementInternals so a selector inside a
 * `<form>` submits its `value` (or `on`) under `name` while
 * selected, follows form reset and `<fieldset disabled>`. It has
 * no constraint validation (no `required`): it is always valid.
 * Hosts that drive selection at the dataset level should ignore
 * the form value and consume the events instead.
 *
 * Accessible name: `label`, else slotted content that has text (an
 * icon alone does not name the checkbox), else a generated name.
 *
 * Theming: every visual value is a `--mj-row-selector-*` token
 * with library fallbacks. Tokens override per-instance.
 *
 * Docking + anchoring: inherited from MjElement.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
  gap: var(--mj-space-2);
  font: inherit;
  color: var(--mj-row-selector-color, var(--mj-text));
}

/*
 * Disabled by the attribute or by a <fieldset disabled> (a form-associated
 * element matches :disabled then). The host keeps the pointer, unlike the
 * base control rule, so a click on a disabled selector is still stopped at
 * the wrap and never falls through to the row underneath.
 */
:host([disabled]),
:host(:disabled) {
  opacity: 0.55;
  pointer-events: auto;
  cursor: not-allowed;
}

:host([disabled]) .wrap,
:host(:disabled) .wrap {
  cursor: not-allowed;
}

:host([disabled]) .wrap:hover,
:host(:disabled) .wrap:hover {
  background: transparent;
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
        // Shift state of the click that caused the pending change.
        this._last_shift_key = false;
        // `selected` as authored, restored by a form reset.
        this._default_selected = null;
        // Disabled through an ancestor <fieldset disabled>.
        this._form_disabled = false;
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
        if (this._default_selected === null) {
            this._default_selected = this.hasAttribute("selected");
        }
        if (this._checkbox !== null) {
            this.listen(this._checkbox, "change", (event) => {
                this._on_native_change(event);
            });
            /*
             * The checkbox is an implementation detail. Its native `input`
             * event is composed, so without this it would reach listeners
             * on the host (and on a containing grid) with no detail.
             * Selection changes are reported through `mj-row-select-change`.
             */
            this.listen(this._checkbox, "input", (event) => {
                event.stopPropagation();
            });
        }
        if (this._wrap !== null) {
            /*
             * A click anywhere on the control (checkbox, label text,
             * padding) toggles it and must not also reach the row it
             * sits in, where it would trigger row navigation or row
             * selection. Stopping it on the wrapping <label> covers
             * every one of those targets; the label's own activation
             * of the checkbox is unaffected.
             */
            this.listen(this._wrap, "click", (event) => {
                if (event.target !== this._checkbox) {
                    this._last_shift_key = event.shiftKey === true;
                } else {
                    // Also reached by the click the <label> forwards
                    // to the checkbox, which may carry no modifiers.
                    this._last_shift_key = this._last_shift_key || event.shiftKey === true;
                }
                event.stopPropagation();
            });
        }
        const slot = this.$("slot");
        if (slot !== null) {
            this.listen(slot, "slotchange", () => {
                this._sync();
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

    /* ----- form-associated callbacks ----- */

    /* A form reset returns the selector to its authored state. */
    formResetCallback() {
        const initial = this._default_selected === true;
        this.removeAttribute("indeterminate");
        if (initial === true) {
            this.setAttribute("selected", "");
        } else {
            this.removeAttribute("selected");
        }
        this._sync();
        return;
    }

    /* An ancestor <fieldset disabled> disables the inner checkbox. */
    formDisabledCallback(disabled) {
        this._form_disabled = disabled === true;
        this._sync();
        return;
    }

    /* Session restore / autofill hands back the submitted value. */
    formStateRestoreCallback(state, reason) {
        if (state !== null && state !== undefined) {
            this.setAttribute("selected", "");
        } else {
            this.removeAttribute("selected");
        }
        this._sync();
        return;
    }

    _on_native_change(event) {
        const previously_indeterminate = this.hasAttribute("indeterminate");
        let next_selected = this._checkbox.checked === true;
        const shift_key = this._last_shift_key;
        this._last_shift_key = false;
        /*
         * Activation clears any indeterminate state regardless of
         * mode and always selects: the browser toggles `checked`,
         * which would unselect a control that was both selected and
         * indeterminate.
         */
        if (previously_indeterminate === true) {
            this.removeAttribute("indeterminate");
            next_selected = true;
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
                // Lets a host implement shift-click range selection.
                shiftKey: shift_key,
            },
            { bubbles: true, composed: true },
        );
        return;
    }

    _sync() {
        const selected = this.hasAttribute("selected");
        const indeterminate = this.hasAttribute("indeterminate");
        const has_slotted = this._has_slotted_label();
        const has_slotted_name = this._has_slotted_name();
        if (this._checkbox !== null) {
            this._checkbox.checked = selected;
            this._checkbox.indeterminate = indeterminate;
            if (this.hasAttribute("disabled") === true || this._form_disabled === true) {
                this._checkbox.setAttribute("disabled", "");
            } else {
                this._checkbox.removeAttribute("disabled");
            }
            const explicit = this.getAttribute("label");
            if (explicit !== null && explicit.length > 0) {
                this._checkbox.setAttribute("aria-label", explicit);
            } else if (has_slotted_name === true) {
                // The visible slotted label inside the wrapping <label>
                // names the checkbox; a generated name would disagree
                // with what is on screen. Slotted content without text
                // (an icon alone) names nothing, so it falls through to
                // the generated name.
                this._checkbox.removeAttribute("aria-label");
            } else {
                this._checkbox.setAttribute("aria-label", this._aria_label());
            }
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
            this._label_el.hidden = has_slotted === false;
        }
        if (this._internals !== null) {
            const form_value = selected === true ? (this.value || "on") : null;
            this._internals.setFormValue(form_value);
        }
        return;
    }

    /*
     * True when the slotted content would give the wrapping <label>
     * a text name: non-blank text, or an element that is not hidden
     * from assistive technology and has text, `aria-label`, or (an
     * image) `alt`.
     */
    _has_slotted_name() {
        const slot = this.$("slot");
        let named = false;
        if (slot !== null) {
            const assigned = slot.assignedNodes({ flatten: true });
            for (const node of assigned) {
                if (named === false && this._node_has_name(node) === true) {
                    named = true;
                }
            }
        }
        return named;
    }

    _node_has_name(node) {
        let named = false;
        if (node.nodeType === Node.TEXT_NODE) {
            named = node.textContent.trim().length > 0;
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const hidden = node.getAttribute("aria-hidden") === "true" || node.hasAttribute("hidden") === true;
            if (hidden === false) {
                const aria_label = node.getAttribute("aria-label");
                const alt = node.localName === "img" ? node.getAttribute("alt") : null;
                if (aria_label !== null && aria_label.trim().length > 0) {
                    named = true;
                } else if (alt !== null && alt.trim().length > 0) {
                    named = true;
                } else {
                    for (const child of node.childNodes) {
                        if (named === false && this._node_has_name(child) === true) {
                            named = true;
                        }
                    }
                }
            }
        }
        return named;
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

    /*
     * The generated name used when the host gives neither a `label`
     * attribute nor a slotted label. Hosts should prefer `label`
     * (e.g. the row's title): it is the localisable path and avoids
     * announcing raw row ids.
     */
    _aria_label() {
        if (this.mode === "all") {
            const count = this.getAttribute("count") || "";
            return count.length > 0 ? t("mj.rowSelector.selectAllCount", { count: count }) : t("core.selectAll");
        }
        return t("mj.rowSelector.selectRow");
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
