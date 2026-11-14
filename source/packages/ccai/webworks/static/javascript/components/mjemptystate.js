/*
 * mjemptystate.js
 *
 * <mj-empty-state> -- displays a meaningful no-content message with an optional
 * illustration, heading, description, and action buttons.
 *
 * Each region is shown only when it has content: the illustration when
 * something is slotted into it (and `show-illustration` is not "false"), the
 * heading when the `heading` attribute or the `heading` slot provides text,
 * the description and the actions when something is slotted into them. An
 * empty region takes no room, so the gap between the regions stays even.
 */

import { MjElement } from "../core/mjelement.js";

const DEFAULT_HEADING_LEVEL = 3;

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

.empty {
  display: none;
}
`;

export class MjEmptyState extends MjElement {
  static tagName = "mj-empty-state";
  static styles = STYLES;
  static watched = ["heading", "heading-level", "compact", "show-illustration"];

  constructor() {
    super()
    this._headingEl = null
    this._headingText = null
  }

  render() {
    const markup = `
      <div class="root" part="root">
        <div class="illustration empty" part="illustration">
          <slot name="illustration"></slot>
        </div>
        <h3 class="heading-el" part="heading">
          <slot name="heading"><span class="heading-text"></span></slot>
        </h3>
        <div class="description empty" part="description">
          <slot name="description"></slot>
        </div>
        <div class="actions empty" part="actions">
          <slot name="actions"></slot>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._headingEl = this.$(".heading-el")
    this._headingText = this.$(".heading-text")

    /* slotchange bubbles to the shadow root; it survives a heading-level swap. */
    this.listen(this.shadowRoot, "slotchange", this._syncRegions.bind(this))

    this._updateHeading()
    this._syncRegions()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._headingEl === undefined || this._headingEl === null) {
      return
    }
    if (name === "heading" || name === "heading-level") {
      this._updateHeading()
    }
    return
  }

  /*
   * True when something is assigned to the named slot. Not flattened: a
   * flattened unassigned slot reports its fallback content instead.
   */
  _slotHasContent(name) {
    const slot = this.$(`slot[name='${name}']`)
    const hasContent = slot !== null && slot.assignedNodes().length > 0
    return hasContent
  }

  /* Show each region only while it has content. */
  _syncRegions() {
    const illustration = this.$(".illustration")
    const description = this.$(".description")
    const actions = this.$(".actions")

    if (illustration !== null) {
      illustration.classList.toggle("empty", this._slotHasContent("illustration") === false)
    }
    if (description !== null) {
      description.classList.toggle("empty", this._slotHasContent("description") === false)
    }
    if (actions !== null) {
      actions.classList.toggle("empty", this._slotHasContent("actions") === false)
    }

    if (this._headingEl !== null) {
      const heading = this.getAttribute("heading") || ""
      const present = heading.length > 0 || this._slotHasContent("heading") === true
      this._headingEl.hidden = present === false
    }
    return
  }

  /* The heading level from `heading-level`, limited to 1-6. */
  _headingLevel() {
    const parsed = parseInt(this.getAttribute("heading-level") || "", 10)
    let level = DEFAULT_HEADING_LEVEL
    if (Number.isNaN(parsed) === false && parsed >= 1 && parsed <= 6) {
      level = parsed
    }
    return level
  }

  /*
   * Bring the heading element in line with `heading-level` (replacing it,
   * and moving its slot across, when the level changes) and the `heading`
   * text, which is the fallback content of the heading slot.
   */
  _updateHeading() {
    const tagName = `h${this._headingLevel()}`

    if (this._headingEl.localName !== tagName) {
      const replacement = document.createElement(tagName)
      replacement.className = "heading-el"
      replacement.setAttribute("part", "heading")
      while (this._headingEl.firstChild !== null) {
        replacement.appendChild(this._headingEl.firstChild)
      }
      this._headingEl.replaceWith(replacement)
      this._headingEl = replacement
    }

    this._headingText.textContent = this.getAttribute("heading") || ""
    this._syncRegions()
    return
  }

  get hasActions() {
    const hasActions = this._slotHasContent("actions")
    return hasActions
  }
}
