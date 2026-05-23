/*
 * mjchip.js
 *
 * <mj-chip> -- compact pill for filters, tags, and token inputs.
 * Covers static (display), removable (delete button), and selectable
 * (checkbox toggle) interaction modes.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host { display: inline-flex; }

.chip {
  display: inline-flex; align-items: center;
  gap: var(--mj-chip-gap, var(--mj-space-1));
  padding-block: var(--mj-chip-padding-block, var(--mj-space-1));
  padding-inline: var(--mj-chip-padding-inline, var(--mj-space-3));
  background: var(--mj-chip-bg, var(--mj-bg-muted));
  color: var(--mj-chip-color, var(--mj-text));
  border: var(--mj-chip-border-width, 1px) solid var(--mj-chip-border-color, var(--mj-border));
  border-radius: var(--mj-chip-border-radius, 9999px);
  font: inherit; font-size: var(--mj-font-size-sm);
  line-height: 1.25;
  cursor: default;
  user-select: none;
  white-space: nowrap;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
}

/* sizes */
:host([size="sm"]) .chip { font-size: var(--mj-font-size-xs); padding-block: 0.125rem; padding-inline: var(--mj-space-2); }
:host([size="lg"]) .chip { font-size: var(--mj-font-size-md); padding-block: var(--mj-space-2); padding-inline: var(--mj-space-4); }

/* selectable hover/active */
:host([mode="selectable"]) .chip { cursor: pointer; }
:host([mode="selectable"]) .chip:hover:not([aria-disabled="true"]) { background: var(--mj-bg-subtle); border-color: var(--mj-border-strong); }
:host([mode="selectable"]) .chip:active:not([aria-disabled="true"]) { background: var(--mj-bg-muted); }
:host([mode="selectable"]) .chip:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }

/* selected */
:host([mode="selectable"][selected]) .chip {
  background: var(--mj-chip-selected-bg, var(--mj-accent));
  color: var(--mj-chip-selected-color, var(--mj-text-on-accent));
  border-color: var(--mj-accent);
}
:host([mode="selectable"][selected]) .check { display: inline-flex; }

/* disabled */
:host([disabled]) .chip { opacity: var(--mj-chip-disabled-opacity, 0.45); pointer-events: none; }

/* icons & check */
.leading-icon { display: inline-flex; align-items: center; }
.check { display: none; width: 0.875rem; height: 0.875rem; }
.check svg { width: 100%; height: 100%; }

/* remove button */
.remove {
  display: inline-flex; align-items: center; justify-content: center;
  width: var(--mj-chip-remove-size, 1.125rem);
  height: var(--mj-chip-remove-size, 1.125rem);
  padding: 0; margin-inline-start: var(--mj-space-1);
  background: transparent; border: none; border-radius: 50%;
  cursor: pointer; color: inherit; flex-shrink: 0;
}
.remove:hover { background: rgba(0,0,0,0.12); }
.remove:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-chip-focus-ring-color, var(--mj-focus-ring)); outline-offset: 1px; }
.remove svg { width: 0.75rem; height: 0.75rem; }
:host(:not([mode="removable"])) .remove { display: none; }
`;

export class MjChip extends MjElement {
  static tagName = "mj-chip";
  static styles = STYLES;
  static watched = ["mode", "selected", "disabled", "value", "size", "remove-label", "color"];

  render() {
    const mode = this.getAttribute("mode") || "static"
    const markup = `
      <div class="chip" part="chip">
        <span class="leading-icon" part="leading-icon"><slot name="leading-icon"></slot></span>
        <span class="check" part="check" aria-hidden="true">
          <svg viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M13.707 4.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-3-3a1 1 0 011.414-1.414L6 10.586l6.293-6.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
        </span>
        <span class="label" part="label"><slot></slot></span>
        <button class="remove" part="remove" type="button">
          <svg aria-hidden="true" viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L8 6.586l2.293-2.293a1 1 0 111.414 1.414L9.414 8l2.293 2.293a1 1 0 01-1.414 1.414L8 9.414l-2.293 2.293a1 1 0 01-1.414-1.414L6.586 8 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
        </button>
      </div>
    `
    return markup
  }

  afterRender() {
    this._chipEl = this.$(".chip")
    this._removeBtn = this.$(".remove")
    this.listen(this._removeBtn, "click", this._onRemove.bind(this))
    this.listen(this._removeBtn, "keydown", this._onRemoveKey.bind(this))
    this.listen(this._chipEl, "click", this._onChipClick.bind(this))
    this.listen(this._chipEl, "keydown", this._onChipKey.bind(this))
    this._syncMode()
    this._syncRemoveLabel()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._chipEl === undefined) {
      return
    }
    if (name === "mode") {
      this._syncMode()
    }
    if (name === "selected") {
      this._syncSelected()
    }
    if (name === "disabled") {
      this._syncDisabled()
    }
    if (name === "color") {
      this._syncColor()
    }
    return
  }

  _syncMode() {
    const mode = this.getAttribute("mode") || "static"
    const chip = this._chipEl
    if (chip === null) {
      return
    }

    if (mode === "selectable") {
      chip.setAttribute("role", "checkbox")
      chip.setAttribute("tabindex", "0")
      this._syncSelected()
    } else if (mode === "removable") {
      chip.removeAttribute("role")
      chip.removeAttribute("tabindex")
      chip.removeAttribute("aria-checked")
      this._syncRemoveLabel()
    } else {
      chip.removeAttribute("role")
      chip.removeAttribute("tabindex")
      chip.removeAttribute("aria-checked")
    }

    this._syncDisabled()
    this._syncColor()
    return
  }

  _syncSelected() {
    const chip = this._chipEl
    if (chip === null) {
      return
    }
    const selected = this.hasAttribute("selected")
    chip.setAttribute("aria-checked", selected === true ? "true" : "false")
    return
  }

  _syncDisabled() {
    const chip = this._chipEl
    if (chip === null) {
      return
    }
    const disabled = this.hasAttribute("disabled")
    if (disabled === true) {
      chip.setAttribute("aria-disabled", "true")
    } else {
      chip.removeAttribute("aria-disabled")
    }
    if (this._removeBtn !== null) {
      this._removeBtn.disabled = disabled
    }
    return
  }

  _syncRemoveLabel() {
    const removeBtn = this._removeBtn
    if (removeBtn === null) {
      return
    }
    const explicit = this.getAttribute("remove-label")
    const label = (explicit !== null && explicit.length > 0)
      ? explicit
      : `Remove ${this.labelText}`
    removeBtn.setAttribute("aria-label", label)
    return
  }

  _syncColor() {
    const color = this.getAttribute("color") || ""
    if (color.length > 0) {
      this.style.setProperty("--mj-chip-bg", color)
    } else {
      this.style.removeProperty("--mj-chip-bg")
    }
    return
  }

  _onRemove() {
    if (this.hasAttribute("disabled")) {
      return
    }
    const proceed = this.emit("mj-chip-remove", { value: this.getAttribute("value") || "", labelText: this.labelText }, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.remove()
    return
  }

  _onRemoveKey(event) {
    if (event.key === "Backspace" || event.key === "Delete") {
      this._onRemove()
    }
    return
  }

  _onChipClick() {
    const mode = this.getAttribute("mode") || "static"
    if (mode !== "selectable") {
      return
    }
    if (this.hasAttribute("disabled")) {
      return
    }
    this._toggleSelected()
    return
  }

  _onChipKey(event) {
    const mode = this.getAttribute("mode") || "static"
    if (mode === "selectable") {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        this._toggleSelected()
      }
    }
    if (mode === "removable") {
      if (event.key === "Backspace" || event.key === "Delete") {
        this._onRemove()
      }
    }
    return
  }

  _toggleSelected() {
    const nextSelected = !this.hasAttribute("selected")
    const value = this.getAttribute("value") || ""
    const proceed = this.emit("mj-chip-select", { value: value, selected: nextSelected }, { cancelable: true })
    if (proceed === false) {
      return
    }
    this.reflectBoolean("selected", nextSelected)
    this.emit("mj-chip-change", { value: value, selected: nextSelected })
    return
  }

  get selected() {
    return this.hasAttribute("selected")
  }

  set selected(value) {
    this.reflectBoolean("selected", value === true)
    return
  }

  get labelText() {
    const labelSlot = this.$("slot:not([name])")
    if (labelSlot === null) {
      return this.textContent.trim()
    }
    const assigned = labelSlot.assignedNodes({ flatten: true })
    const text = assigned.map((n) => n.textContent).join("").trim()
    return text
  }
}
