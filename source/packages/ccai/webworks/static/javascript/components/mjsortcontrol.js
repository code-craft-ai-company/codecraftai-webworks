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
 * `cycle` chooses the states and their order as a dash-separated
 * list, e.g. "asc-desc" (two-state) or "desc-asc-none"
 * (descending first). Controls that share a `group` value inside
 * the same document or shadow root sort one dataset: activating
 * one resets the others to "none" (without an event), so the host
 * does not have to hand-roll single-sort bookkeeping.
 *
 * The accessible name is built from three templates that can be
 * replaced for other languages: `label-none`, `label-asc` and
 * `label-desc`; `{label}` in a template is the field label.
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
import { t } from "../core/intl.js";

const DIRECTIONS = ["none", "asc", "desc"];

/*
 * Default accessible-name templates, by current direction and then by the
 * direction the next activation moves to. Used when the `label-*`
 * attribute for the current direction is not set.
 */
const DEFAULT_LABEL_KEYS = {
    none: {
        asc: "mj.sortControl.labelNoneToAsc",
        desc: "mj.sortControl.labelNoneToDesc",
    },
    asc: {
        desc: "mj.sortControl.labelAscToDesc",
        none: "mj.sortControl.labelAscToNone",
    },
    desc: {
        asc: "mj.sortControl.labelDescToAsc",
        none: "mj.sortControl.labelDescToNone",
    },
};

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
    static watched = [
        "field",
        "direction",
        "disabled",
        "label",
        "cycle",
        "group",
        "label-none",
        "label-asc",
        "label-desc",
    ];

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
            /*
             * A native <button> already turns Enter and Space into a
             * click, so the click listener is the only activation path.
             */
            this.listen(this._button, "click", (event) => {
                this._on_activate(event);
            });
        }
        const slot = this.$("slot");
        if (slot !== null) {
            /* The slotted text is part of the accessible name. */
            this.listen(slot, "slotchange", () => {
                this._sync();
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

    /*
     * The directions this control steps through, in order. Parsed
     * from `cycle`; anything unusable falls back to the default
     * none -> asc -> desc.
     */
    _cycle() {
        const raw = this.getAttribute("cycle") || "";
        const steps = [];
        for (const token of raw.split("-")) {
            const step = token.trim().toLowerCase();
            if (DIRECTIONS.indexOf(step) >= 0 && steps.indexOf(step) < 0) {
                steps.push(step);
            }
        }
        const rtnval = steps.length >= 2 ? steps : DIRECTIONS;
        return rtnval;
    }

    /* The direction an activation moves to from `current`. */
    _next_direction(current) {
        const steps = this._cycle();
        const idx = steps.indexOf(current);
        let rtnval = steps[0];
        if (idx >= 0) {
            rtnval = steps[(idx + 1) % steps.length];
        } else if (steps[0] === "none") {
            // Not in the cycle (e.g. host set a state the cycle skips):
            // start from the first sorted state.
            rtnval = steps[1];
        }
        return rtnval;
    }

    /*
     * Reset the other controls of this control's `group` in the same
     * root. They change silently; the host learns the new sort from
     * the event of the control that was activated.
     */
    _reset_group_siblings() {
        const group = this.getAttribute("group");
        if (group === null || group.length === 0) {
            return;
        }
        const root = this.getRootNode();
        const members = root.querySelectorAll("mj-sort-control[group]");
        for (const member of members) {
            if (member !== this && member.getAttribute("group") === group) {
                if (member.getAttribute("direction") !== "none") {
                    member.setAttribute("direction", "none");
                }
            }
        }
        return;
    }

    _on_activate(event) {
        if (this.hasAttribute("disabled") === true) {
            return;
        }
        const current = this.direction;
        const next = this._next_direction(current);
        this._previousDirection = current;
        this.setAttribute("direction", next);
        if (next !== "none") {
            this._reset_group_siblings();
        }
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

    /*
     * The accessible name: the template for the current direction
     * with `{label}` replaced by the field label. The three
     * templates are attributes so a page can supply its language.
     */
    _aria_label() {
        const label_attr = this.getAttribute("label") || this.textContent.trim();
        const field = this.field;
        const subject = label_attr.length > 0 ? label_attr : field;
        const direction = this.direction;
        const next = this._next_direction(direction);

        let template = "";
        if (direction === "asc") {
            template = this.getAttribute("label-asc") || "";
        } else if (direction === "desc") {
            template = this.getAttribute("label-desc") || "";
        } else {
            template = this.getAttribute("label-none") || "";
        }

        if (template.length === 0) {
            const key = DEFAULT_LABEL_KEYS[direction][next];
            template = key !== undefined ? t(key) : "{label}";
        }

        const rtnval = template.split("{label}").join(subject);
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
