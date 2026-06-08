/*
 * mjsortcontrol.js
 *
 * <mj-sort-control> -- a sort header indicator + control. Click or
 * keyboard-activate to cycle the sort direction through
 * none -> asc -> desc -> none for a named field. Emits
 * `mj-sort-change` with `{ field, direction, previousDirection }`
 * on every transition so a host (DataTable, list view, ...)
 * can re-sort.
 *
 * The control is independently placeable -- it lives wherever it
 * is slotted, not just inside a table header. That is what makes
 * it a "Sort control" companion (5.8 in the web-component plan)
 * rather than table-internal UI.
 *
 * WAI-ARIA: button role; aria-pressed reflects sorted-ness;
 * aria-label includes the field label + active direction so
 * screen readers announce changes.
 *
 * Theming: every visual value resolves through a token
 * (`--mj-sort-control-*`) defaulting to library tokens. No
 * hard-coded colors, sizes, or fonts.
 *
 * Docking + anchoring: inherited from MjElement -- adding
 * `dock="start"` / `anchor="top-end"` Just Works.
 */

import { MjElement } from "../core/mjelement.js";

const DIRECTIONS = ["none", "asc", "desc"];

const STYLES = `
:host {
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
  font: inherit;
  color: var(--mj-sort-control-color, var(--mj-text));
}

:host([disabled]) {
  opacity: 0.55;
  pointer-events: none;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--mj-space-1);
  min-height: var(--mj-sort-control-height, var(--mj-control-height-sm));
  padding: 0 var(--mj-space-2);
  font: inherit;
  font-weight: var(--mj-sort-control-font-weight, var(--mj-font-weight-medium));
  color: inherit;
  background: var(--mj-sort-control-bg, transparent);
  border: 1px solid var(--mj-sort-control-border-color, transparent);
  border-radius: var(--mj-sort-control-border-radius, var(--mj-radius-sm));
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.btn:hover {
  background: var(--mj-sort-control-bg-hover, var(--mj-bg-muted));
}

.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-sort-control-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

:host([direction="asc"]) .btn,
:host([direction="desc"]) .btn {
  background: var(--mj-sort-control-bg-active, var(--mj-bg-muted));
  color: var(--mj-sort-control-color-active, var(--mj-accent));
}

.label {
  display: inline-flex;
  align-items: center;
}

.indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--mj-sort-control-icon-size, 0.875rem);
  height: var(--mj-sort-control-icon-size, 0.875rem);
  font-size: var(--mj-sort-control-icon-size, 0.875rem);
  line-height: 1;
  color: var(--mj-sort-control-indicator-color, currentColor);
}

.indicator svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

:host([direction="none"]) .indicator { opacity: 0.45; }

@media (prefers-reduced-motion: no-preference) {
  .indicator { transition: transform var(--mj-motion-fast, 120ms) var(--mj-motion-ease, ease); }
}
`;

const ICON_NONE = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1.5 9 4.5 H3z M6 10.5 3 7.5 H9z"/></svg>';
const ICON_ASC = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 2 10 7H2z"/></svg>';
const ICON_DESC = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 10 2 5H10z"/></svg>';

export class MjSortControl extends MjElement {
    static tagName = "mj-sort-control";
    static styles = STYLES;
    static watched = ["field", "direction", "disabled", "label"];

    constructor() {
        super();
        this._button = null;
        this._indicator = null;
        this._previousDirection = "none";
    }

    render() {
        const markup = `
            <button class="btn" part="button" type="button">
                <span class="label" part="label"><slot></slot></span>
                <span class="indicator" part="indicator"></span>
            </button>
        `;
        return markup;
    }

    afterRender() {
        this._button = this.$(".btn");
        this._indicator = this.$(".indicator");
        if (this._button !== null) {
            this._button.addEventListener("click", (event) => {
                this._on_activate(event);
            });
            this._button.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    this._on_activate(event);
                }
            });
        }
        if (this.getAttribute("direction") === null) {
            this.setAttribute("direction", "none");
        }
        this._previousDirection = this.getAttribute("direction") || "none";
        this._sync();
        return;
    }

    onAttributeChanged(name, oldValue, newValue) {
        if (this._button === null) {
            return;
        }
        this._sync();
        return;
    }

    _on_activate(event) {
        if (this.hasAttribute("disabled") === true) {
            return;
        }
        const current = this.direction;
        const idx = DIRECTIONS.indexOf(current);
        const next_idx = idx < 0 ? 1 : (idx + 1) % DIRECTIONS.length;
        const next = DIRECTIONS[next_idx];
        this._previousDirection = current;
        this.setAttribute("direction", next);
        this.emit(
            "mj-sort-change",
            {
                field: this.field,
                direction: next,
                previousDirection: current,
            },
            { bubbles: true, composed: true },
        );
        return;
    }

    _sync() {
        const direction = this.direction;
        const label = this._aria_label();
        if (this._indicator !== null) {
            if (direction === "asc") {
                this._indicator.innerHTML = ICON_ASC;
            } else if (direction === "desc") {
                this._indicator.innerHTML = ICON_DESC;
            } else {
                this._indicator.innerHTML = ICON_NONE;
            }
        }
        if (this._button !== null) {
            this._button.setAttribute("aria-label", label);
            this._button.setAttribute(
                "aria-pressed",
                direction === "none" ? "false" : "true",
            );
            if (this.hasAttribute("disabled") === true) {
                this._button.setAttribute("disabled", "");
            } else {
                this._button.removeAttribute("disabled");
            }
        }
        return;
    }

    _aria_label() {
        const label_attr = this.getAttribute("label") || this.textContent.trim();
        const field = this.field;
        const subject = label_attr.length > 0 ? label_attr : field;
        const direction = this.direction;
        let suffix = "";
        if (direction === "asc") {
            suffix = ", sorted ascending. Activate to sort descending.";
        } else if (direction === "desc") {
            suffix = ", sorted descending. Activate to clear sort.";
        } else {
            suffix = ", not sorted. Activate to sort ascending.";
        }
        const rtnval = "Sort by " + subject + suffix;
        return rtnval;
    }

    get field() {
        const rtnval = this.getAttribute("field") || "";
        return rtnval;
    }

    set field(value) {
        this.setAttribute("field", String(value));
        return;
    }

    get direction() {
        const raw = this.getAttribute("direction") || "none";
        if (DIRECTIONS.indexOf(raw) < 0) {
            return "none";
        }
        return raw;
    }

    set direction(value) {
        const normalized = DIRECTIONS.indexOf(value) >= 0 ? value : "none";
        this.setAttribute("direction", normalized);
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

    /*
     * Reset the control to "none" without emitting a change event.
     * The host may call this after a controlled sort change so the
     * UI matches state without echoing back the event.
     */
    reset() {
        this.setAttribute("direction", "none");
        return;
    }
}
