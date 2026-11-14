/*
 * mjdisclosure.js
 *
 * <mj-disclosure> -- a single show/hide region with a trigger button and
 * collapsible content panel. Implements the ARIA button + region pattern with
 * animated height transitions.
 *
 * The `open` attribute is the state. The panel is in one of four phases:
 *   closed    hidden (display: none): its content is neither focusable nor
 *             exposed to assistive technology
 *   opening   visible, max-block-size animating up to the content height
 *   open      visible, no height limit, overflow visible
 *   closing   visible, max-block-size animating down to zero
 * Only one transition is ever pending; a state change during a transition
 * cancels it and starts the opposite one from the height reached so far.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";

/* Extra time allowed for `transitionend` before the fallback timer acts. */
const TRANSITION_GRACE_MS = 60;

/* Heading level used for a disclosure that is a panel of an mj-accordion. */
const ACCORDION_HEADING_LEVEL = 3;

const STYLES = `
:host {
  display: block;
}

/*
 * disabled blocks the trigger only. The shared base sheet turns pointer
 * events off for every disabled host, which would make the content of an
 * open panel unclickable; undo that here.
 */
:host([disabled]) {
  pointer-events: auto;
  cursor: auto;
}

.heading {
  margin: 0;
}

.trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin: 0;
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

.summary-text {
  flex: 1 1 auto;
  min-inline-size: 0;
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

.panel {
  overflow: hidden;
  transition: max-block-size var(--mj-disclosure-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}

.panel[data-phase="open"] {
  overflow: visible;
}

:host([animated="false"]) .panel {
  transition: none;
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
    this._trigger = null
    this._panel = null
    this._headingWrap = null
    this._headingText = null

    /* The state the panel shows or is animating toward. */
    this._shownOpen = false

    /* { onEnd, timer } while a height transition is running, else null. */
    this._pendingTransition = null
  }

  render() {
    const markup = html`
      <div class="wrapper">
        <div class="heading">
          <button
            class="trigger"
            part="trigger"
            type="button"
            id="${this._triggerId}"
            aria-expanded="false"
            aria-controls="${this._panelId}"
          >
            <span class="summary-text"><slot name="summary"><span class="heading-text"></span></slot></span>
            <svg class="indicator" part="indicator" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
        <div
          class="panel"
          part="panel"
          id="${this._panelId}"
          role="region"
          aria-labelledby="${this._triggerId}"
          data-phase="closed"
          hidden
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
    this._headingWrap = this.$(".heading")
    this._headingText = this.$(".heading-text")
    this.listen(this._trigger, "click", this._onTriggerClick.bind(this))
    this._syncState()
    this._showPanel(this.hasAttribute("open"))
    return
  }

  onConnected() {
    this.onTeardown(() => {
      this._cancelPendingTransition()
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._trigger === undefined || this._trigger === null) {
      return
    }

    if (name === "open") {
      this._applyOpenState(newValue !== null)
    } else {
      this._syncState()
    }
    return
  }

  /*
   * The level of the heading that wraps the trigger: the `heading-level`
   * attribute (1-6), or -- for a panel of an mj-accordion, where the pattern
   * requires a heading -- level 3. null means no heading semantics.
   */
  _headingLevel() {
    const attribute = this.getAttribute("heading-level")
    let level = null

    if (attribute !== null) {
      const parsed = parseInt(attribute, 10)
      if (String(parsed) === attribute.trim() && parsed >= 1 && parsed <= 6) {
        level = parsed
      }
    } else {
      const parent = this.parentNode
      const inAccordion = parent !== null && parent !== undefined && parent.localName === "mj-accordion"
      if (inAccordion === true) {
        level = ACCORDION_HEADING_LEVEL
      }
    }

    return level
  }

  /* Everything except the open state: trigger ARIA, heading text and level. */
  _syncState() {
    if (this._trigger === null || this._trigger === undefined) {
      return
    }

    const disabled = this.hasAttribute("disabled")
    const heading = this.getAttribute("heading") || ""
    const level = this._headingLevel()

    if (disabled === true) {
      this._trigger.setAttribute("aria-disabled", "true")
      this._trigger.setAttribute("tabindex", "-1")
    } else {
      this._trigger.removeAttribute("aria-disabled")
      this._trigger.setAttribute("tabindex", "0")
    }

    /*
     * The heading text is the fallback content of the summary slot, so
     * slotted summary content replaces it and the slot itself is never lost.
     */
    this._headingText.textContent = heading

    if (level !== null) {
      this._headingWrap.setAttribute("role", "heading")
      this._headingWrap.setAttribute("aria-level", String(level))
    } else {
      this._headingWrap.removeAttribute("role")
      this._headingWrap.removeAttribute("aria-level")
    }
    return
  }

  /* ----- open / close ----- */

  /* Put the panel straight into its final open or closed phase. */
  _showPanel(open) {
    this._cancelPendingTransition()
    this._shownOpen = open
    this._trigger.setAttribute("aria-expanded", open === true ? "true" : "false")
    this._panel.style.maxBlockSize = ""

    if (open === true) {
      this._panel.hidden = false
      this._panel.setAttribute("data-phase", "open")
    } else {
      this._panel.hidden = true
      this._panel.setAttribute("data-phase", "closed")
    }
    return
  }

  /* The duration of the panel's height transition in milliseconds. */
  _transitionDuration() {
    let duration = 0

    if (this.getAttribute("animated") !== "false") {
      const computed = window.getComputedStyle(this._panel)
      const seconds = parseFloat(computed.transitionDuration)
      const delay = parseFloat(computed.transitionDelay)
      if (Number.isNaN(seconds) === false) {
        duration = seconds * 1000 + (Number.isNaN(delay) === false ? delay * 1000 : 0)
      }
    }

    return duration
  }

  _cancelPendingTransition() {
    if (this._pendingTransition !== null) {
      this._panel.removeEventListener("transitionend", this._pendingTransition.onEnd)
      window.clearTimeout(this._pendingTransition.timer)
      this._pendingTransition = null
    }
    return
  }

  /*
   * Run `finish` once when the panel's height transition ends. A timer backs
   * the event up: `transitionend` never fires when the height did not
   * actually change or the element is not rendered.
   */
  _awaitTransition(duration, finish) {
    const onEnd = (event) => {
      const forPanel = event === undefined || event.target === this._panel
      if (forPanel === true) {
        this._cancelPendingTransition()
        finish()
      }
    }

    this._pendingTransition = {
      onEnd: onEnd,
      timer: window.setTimeout(onEnd, duration + TRANSITION_GRACE_MS)
    }
    this._panel.addEventListener("transitionend", this._pendingTransition.onEnd)
    return
  }

  /*
   * Move the panel to the open or closed state, animating the height when
   * that is possible. Idempotent: asking for the state the panel already
   * shows (or is animating toward) does nothing, so a replayed attribute
   * change neither restarts the animation nor repeats the event.
   */
  _applyOpenState(open) {
    if (this._trigger === null || this._trigger === undefined || open === this._shownOpen) {
      return
    }

    /* The height reached so far, before the pending transition is dropped. */
    const wasHidden = this._panel.hidden === true
    const currentHeight = wasHidden === true ? 0 : this._panel.getBoundingClientRect().height

    this._cancelPendingTransition()
    this._shownOpen = open
    this._trigger.setAttribute("aria-expanded", open === true ? "true" : "false")

    const duration = this._transitionDuration()

    if (open === true) {
      this._panel.hidden = false
      this._panel.setAttribute("data-phase", "opening")
      const targetHeight = this._panel.scrollHeight

      if (duration === 0 || targetHeight === 0) {
        /* Nothing to animate (no motion, or not rendered): open at once. */
        this._finishOpen()
      } else {
        /* Start from the current height; the read flushes it as the start value. */
        this._panel.style.maxBlockSize = `${currentHeight}px`
        this._panel.getBoundingClientRect()
        this._panel.style.maxBlockSize = `${targetHeight}px`
        this._awaitTransition(duration, () => {
          this._finishOpen()
        })
      }
    } else {
      this._panel.setAttribute("data-phase", "closing")

      if (duration === 0 || currentHeight === 0) {
        this._finishClose()
      } else {
        this._panel.style.maxBlockSize = `${currentHeight}px`
        this._panel.getBoundingClientRect()
        this._panel.style.maxBlockSize = "0px"
        this._awaitTransition(duration, () => {
          this._finishClose()
        })
      }
    }
    return
  }

  _finishOpen() {
    this._panel.style.maxBlockSize = ""
    this._panel.setAttribute("data-phase", "open")
    this.emit("mj-disclosure-open", {})
    return
  }

  /*
   * A closed panel is taken out of rendering altogether, which removes its
   * content from the tab order and from the accessibility tree.
   */
  _finishClose() {
    this._panel.hidden = true
    this._panel.style.maxBlockSize = ""
    this._panel.setAttribute("data-phase", "closed")
    this.emit("mj-disclosure-close", {})
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
    this.reflectBoolean("open", Boolean(value))
    return
  }

  get panelElement() {
    return this._panel || null
  }

  get triggerElement() {
    return this._trigger || null
  }

  focus(options) {
    if (this._trigger !== null && this._trigger !== undefined) {
      this._trigger.focus(options)
    }
    return
  }
}
