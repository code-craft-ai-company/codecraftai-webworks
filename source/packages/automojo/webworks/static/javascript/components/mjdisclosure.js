/*
 * mjdisclosure.js
 *
 * <mj-disclosure> -- a single show/hide region with a trigger button and
 * collapsible content panel. Implements the ARIA button + region pattern with
 * animated height transitions.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--mj-disclosure-trigger-padding, var(--mj-space-3) var(--mj-space-4));
  background: var(--mj-disclosure-trigger-bg, transparent);
  color: var(--mj-disclosure-trigger-color, var(--mj-text));
  border: none;
  border-block-end: 1px solid var(--mj-disclosure-border, var(--mj-border));
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  cursor: pointer;
  text-align: start;
  min-block-size: var(--mj-target-min);
  box-sizing: border-box;
}

.trigger:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([disabled]) .trigger {
  opacity: 0.55;
  cursor: not-allowed;
}

.indicator {
  flex-shrink: 0;
  width: var(--mj-disclosure-indicator-size, 1.25rem);
  height: var(--mj-disclosure-indicator-size, 1.25rem);
  transition: transform var(--mj-motion-fast) var(--mj-motion-ease);
  margin-inline-start: var(--mj-space-2);
}

:host([indicator-position="start"]) .indicator {
  margin-inline-start: 0;
  margin-inline-end: var(--mj-space-2);
  order: -1;
}

:host([open]) .indicator {
  transform: rotate(180deg);
}

:dir(rtl) .indicator {
  transform: scaleX(-1);
}
:dir(rtl) :host([open]) .indicator {
  transform: scaleX(-1) rotate(180deg);
}

.panel {
  overflow: hidden;
  max-block-size: 0;
  transition: max-block-size var(--mj-disclosure-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}

:host([open]) .panel {
  max-block-size: none;
}

.panel-inner {
  padding: var(--mj-disclosure-panel-padding, var(--mj-space-4));
}

@media (prefers-reduced-motion: reduce) {
  .panel { transition: none; }
  .indicator { transition: none; }
}
`;

export class MjDisclosure extends MjElement {
  static tagName = "mj-disclosure";
  static styles = STYLES;
  static watched = ["open", "heading", "heading-level", "disabled", "animated", "indicator-position"];

  constructor() {
    super()
    this._triggerId = nextId("mj-disclosure-trigger")
    this._panelId = nextId("mj-disclosure-panel")
    this._animating = false
  }

  render() {
    const markup = `
      <div class="wrapper">
        <button
          class="trigger"
          part="trigger"
          id="${this._triggerId}"
          aria-expanded="false"
          aria-controls="${this._panelId}"
        >
          <span class="summary-text"><slot name="summary"></slot></span>
          <svg class="indicator" part="indicator" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <div
          class="panel"
          part="panel"
          id="${this._panelId}"
          role="region"
          aria-labelledby="${this._triggerId}"
        >
          <div class="panel-inner"><slot></slot></div>
        </div>
      </div>
    `
    return markup
  }

  afterRender() {
    this._trigger = this.$(".trigger")
    this._panel = this.$(".panel")
    this._summaryText = this.$(".summary-text")
    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this._syncState()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._trigger === undefined) {
      return
    }
    if (name === "open") {
      this._applyOpenState(newValue !== null)
    } else {
      this._syncState()
    }
    return
  }

  _syncState() {
    if (this._trigger === null || this._trigger === undefined) {
      return
    }

    const isOpen = this.hasAttribute("open")
    const disabled = this.hasAttribute("disabled")
    const heading = this.getAttribute("heading") || ""

    this._trigger.setAttribute("aria-expanded", isOpen === true ? "true" : "false")

    if (disabled === true) {
      this._trigger.setAttribute("aria-disabled", "true")
      this._trigger.setAttribute("tabindex", "-1")
    } else {
      this._trigger.removeAttribute("aria-disabled")
      this._trigger.setAttribute("tabindex", "0")
    }

    const summarySlot = this._trigger.querySelector("slot[name='summary']")
    const hasSlottedSummary = summarySlot !== null && summarySlot.assignedNodes().length > 0
    if (hasSlottedSummary === false && heading.length > 0) {
      if (this._summaryText !== null) {
        this._summaryText.textContent = heading
      }
    }

    if (isOpen === true) {
      this._panel.style.maxHeight = "none"
      this._panel.style.overflow = "visible"
    } else {
      this._panel.style.maxHeight = "0"
      this._panel.style.overflow = "hidden"
    }
    return
  }

  _applyOpenState(open) {
    if (this._trigger === null || this._trigger === undefined) {
      return
    }

    this._trigger.setAttribute("aria-expanded", open === true ? "true" : "false")

    const animated = this.getAttribute("animated") !== "false"
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches

    if (open === true) {
      this._panel.style.overflow = "hidden"
      this._panel.style.maxHeight = this._panel.scrollHeight + "px"

      if (animated === true && prefersReduced === false) {
        const onEnd = () => {
          this._panel.removeEventListener("transitionend", onEnd)
          this._panel.style.maxHeight = "none"
          this._panel.style.overflow = "visible"
          this.emit("mj-disclosure-open", {})
        }
        this._panel.addEventListener("transitionend", onEnd)
      } else {
        this._panel.style.maxHeight = "none"
        this._panel.style.overflow = "visible"
        this.emit("mj-disclosure-open", {})
      }
    } else {
      this._panel.style.maxHeight = this._panel.scrollHeight + "px"
      this._panel.style.overflow = "hidden"
      window.requestAnimationFrame(() => {
        this._panel.style.maxHeight = "0"
      })

      if (animated === true && prefersReduced === false) {
        const onEnd = () => {
          this._panel.removeEventListener("transitionend", onEnd)
          this.emit("mj-disclosure-close", {})
        }
        this._panel.addEventListener("transitionend", onEnd)
      } else {
        this._panel.style.maxHeight = "0"
        this.emit("mj-disclosure-close", {})
      }
    }
    return
  }

  _onTriggerClick(event) {
    if (this.hasAttribute("disabled")) {
      return
    }

    const currentOpen = this.hasAttribute("open")
    const proceed = this.emit("mj-disclosure-toggle", { open: !currentOpen }, { cancelable: true })
    if (proceed === false) {
      return
    }

    if (currentOpen === true) {
      this.removeAttribute("open")
    } else {
      this.setAttribute("open", "")
    }
    return
  }

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
    return
  }

  get panelElement() {
    return this._panel || null
  }

  get triggerElement() {
    return this._trigger || null
  }

  focus() {
    if (this._trigger !== null && this._trigger !== undefined) {
      this._trigger.focus()
    }
    return
  }
}
