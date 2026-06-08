/*
 * mjemptystate.js
 *
 * <mj-empty-state> -- displays a meaningful no-content message with an optional
 * illustration, heading, description, and action buttons.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.root {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--mj-empty-state-padding, var(--mj-space-8));
  gap: var(--mj-empty-state-gap, var(--mj-space-4));
  max-inline-size: var(--mj-empty-state-max-width, 24rem);
  margin-inline: auto;
}

:host([compact]) .root {
  padding: var(--mj-space-5);
  gap: var(--mj-space-2);
}

.illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  inline-size: var(--mj-empty-state-illustration-size, 5rem);
  block-size: var(--mj-empty-state-illustration-size, 5rem);
  flex-shrink: 0;
}

:host([compact]) .illustration {
  inline-size: 3rem;
  block-size: 3rem;
}

:host([show-illustration="false"]) .illustration {
  display: none;
}

.heading-el {
  margin: 0;
  font-size: var(--mj-font-size-lg);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-empty-state-heading-color, var(--mj-text));
}

:host([compact]) .heading-el {
  font-size: var(--mj-font-size-md);
}

.description {
  color: var(--mj-empty-state-description-color, var(--mj-text-muted));
  font-size: var(--mj-font-size-sm);
  line-height: var(--mj-line-height);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--mj-space-2);
  justify-content: center;
}

.actions.empty {
  display: none;
}
`;

export class MjEmptyState extends MjElement {
  static tagName = "mj-empty-state";
  static styles = STYLES;
  static watched = ["heading", "heading-level", "compact", "show-illustration"];

  render() {
    const headingLevel = this.getAttribute("heading-level") || "3"
    const heading = this.getAttribute("heading") || ""
    const markup = `
      <div class="root" part="root">
        <div class="illustration" part="illustration">
          <slot name="illustration"></slot>
        </div>
        <h${headingLevel} class="heading-el" part="heading">
          <slot name="heading">${heading}</slot>
        </h${headingLevel}>
        <div class="description" part="description">
          <slot name="description"></slot>
        </div>
        <div class="actions" part="actions">
          <slot name="actions"></slot>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._actionsSlot = this.shadowRoot.querySelector("slot[name='actions']")
    if (this._actionsSlot !== null) {
      this.listen(this._actionsSlot, "slotchange", this._onActionsSlotChange.bind(this))
    }
    this._checkActions()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "heading" || name === "heading-level") {
      this._updateHeading()
    }
    return
  }

  _onActionsSlotChange() {
    this._checkActions()
    return
  }

  _checkActions() {
    const actionsEl = this.$(".actions")
    if (actionsEl === null) {
      return
    }
    const slot = actionsEl.querySelector("slot")
    const hasContent = slot !== null && slot.assignedElements().length > 0
    if (hasContent === true) {
      actionsEl.classList.remove("empty")
    } else {
      actionsEl.classList.add("empty")
    }
    return
  }

  _updateHeading() {
    const headingEl = this.$(".heading-el")
    if (headingEl === null) {
      return
    }
    const level = this.getAttribute("heading-level") || "3"
    const heading = this.getAttribute("heading") || ""
    const slot = headingEl.querySelector("slot[name='heading']")
    if (slot !== null) {
      slot.textContent = heading
    }
    return
  }

  get hasActions() {
    const actionsEl = this.$(".actions")
    if (actionsEl === null) {
      return false
    }
    const slot = actionsEl.querySelector("slot")
    return slot !== null && slot.assignedElements().length > 0
  }
}
