/*
 * mjaccordion.js
 *
 * <mj-accordion> -- groups multiple <mj-disclosure> panels and coordinates
 * their open/closed state per the WAI-ARIA Accordion pattern.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

.root {
  border-radius: var(--mj-accordion-radius, var(--mj-radius-md));
}

:host([bordered]) .root {
  border: 1px solid var(--mj-accordion-border, var(--mj-border));
  overflow: hidden;
}

:host(:not([bordered])) .root {
  display: flex;
  flex-direction: column;
  gap: var(--mj-accordion-gap, 0);
}
`;

export class MjAccordion extends MjElement {
  static tagName = "mj-accordion";
  static styles = STYLES;
  static watched = ["allow-multiple", "bordered", "flush", "disabled"];

  constructor() {
    super()
    this._mutationObserver = null
  }

  render() {
    const markup = `<div class="root" part="root"><slot></slot></div>`
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this.listen(this, "mj-disclosure-toggle", this._onDisclosureToggle.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))
    return
  }

  onConnected() {
    this._mutationObserver = new MutationObserver(() => {
      this._propagateDisabled()
    })
    this._mutationObserver.observe(this, { childList: true })
    return
  }

  onDisconnected() {
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "disabled") {
      this._propagateDisabled()
    }
    if (name === "allow-multiple" && newValue === null) {
      this._enforceSingleOpen()
    }
    return
  }

  _propagateDisabled() {
    const panels = this.panels
    const disabled = this.hasAttribute("disabled")
    for (let i = 0; i < panels.length; i = i + 1) {
      if (disabled === true) {
        panels[i].setAttribute("disabled", "")
      } else {
        panels[i].removeAttribute("disabled")
      }
    }
    return
  }

  _enforceSingleOpen() {
    const panels = this.panels
    let foundOpen = false
    for (let i = 0; i < panels.length; i = i + 1) {
      if (panels[i].hasAttribute("open") === true) {
        if (foundOpen === true) {
          panels[i].open = false
        } else {
          foundOpen = true
        }
      }
    }
    return
  }

  _onDisclosureToggle(event) {
    const allowMultiple = this.hasAttribute("allow-multiple")
    if (allowMultiple === true) {
      return
    }

    const openingPanel = event.target
    if (event.detail.open !== true) {
      return
    }

    const panels = this.panels
    for (let i = 0; i < panels.length; i = i + 1) {
      const panel = panels[i]
      if (panel !== openingPanel && panel.hasAttribute("open") === true) {
        panel.open = false
        this.emit("mj-accordion-close", { panel: panel, index: i })
      }
    }
    return
  }

  _onKeyDown(event) {
    const panels = this.panels
    if (panels.length === 0) {
      return
    }

    const triggers = panels.map((p) => p.triggerElement).filter((t) => t !== null)
    const focused = this.shadowRoot.activeElement || document.activeElement
    const activeIndex = triggers.indexOf(focused)

    if (event.key === "ArrowDown") {
      event.preventDefault()
      const nextIndex = (activeIndex + 1) % triggers.length
      triggers[nextIndex].focus()
    } else if (event.key === "ArrowUp") {
      event.preventDefault()
      const prevIndex = (activeIndex - 1 + triggers.length) % triggers.length
      triggers[prevIndex].focus()
    } else if (event.key === "Home") {
      event.preventDefault()
      triggers[0].focus()
    } else if (event.key === "End") {
      event.preventDefault()
      triggers[triggers.length - 1].focus()
    }
    return
  }

  get panels() {
    const children = Array.from(this.children)
    const disclosures = children.filter((el) => el.tagName.toLowerCase() === "mj-disclosure")
    return disclosures
  }

  get openPanels() {
    const all = this.panels
    const open = all.filter((p) => p.hasAttribute("open"))
    return open
  }
}
