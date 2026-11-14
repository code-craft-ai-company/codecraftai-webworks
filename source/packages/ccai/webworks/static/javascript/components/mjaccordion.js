/*
 * mjaccordion.js
 *
 * <mj-accordion> -- groups multiple <mj-disclosure> panels and coordinates
 * their open/closed state per the WAI-ARIA Accordion pattern.
 *
 * Only DIRECT <mj-disclosure> children are panels of the accordion. A
 * disclosure or accordion nested inside a panel is independent: its toggles
 * and key presses are ignored here.
 *
 * The single-open rule follows the panels' `open` attribute rather than the
 * cancelable toggle event, so it also holds for panels opened from script,
 * for several panels marked open in the markup, and it is not applied to a
 * toggle that a listener cancelled.
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
}

/*
 * disabled blocks the panel triggers only. The shared base sheet turns
 * pointer events off for every disabled host, which would make the content
 * of an open panel unclickable; undo that here.
 */
:host([disabled]) {
  pointer-events: auto;
  cursor: auto;
}

.root {
  position: relative;
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

/*
 * flush: no outer border, radius or gaps, and no inline padding in the
 * panels, so the accordion lines up with the surrounding content. The
 * padding properties are inherited by the mj-disclosure children.
 */
:host([flush]) {
  --mj-disclosure-trigger-padding: var(--mj-space-3) 0;
  --mj-disclosure-panel-padding: var(--mj-space-4) 0;
}

:host([flush]) .root {
  border: none;
  border-radius: 0;
  gap: 0;
}
`;

export class MjAccordion extends MjElement {
  static tagName = "mj-accordion";
  static styles = STYLES;
  static watched = ["allow-multiple", "bordered", "flush", "disabled"];

  constructor() {
    super()
    this._root = null
    this._mutationObserver = null

    /* Panels this accordion disabled; only these are re-enabled by it. */
    this._disabledPanels = new WeakSet()
  }

  render() {
    const markup = `<div class="root" part="root"><slot></slot></div>`
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this.listen(this, "mj-disclosure-open", this._onPanelOpened.bind(this))
    this.listen(this, "mj-disclosure-close", this._onPanelClosed.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))
    return
  }

  onConnected() {
    /*
     * Panels added or removed, and the `open` attribute of every panel.
     * Records about deeper descendants (nested disclosures) are ignored.
     */
    this._mutationObserver = new MutationObserver((records) => {
      this._onMutations(records)
    })
    this._mutationObserver.observe(this, {
      childList: true,
      attributes: true,
      attributeFilter: ["open"],
      subtree: true
    })

    this.onTeardown(() => {
      if (this._mutationObserver !== null) {
        this._mutationObserver.disconnect()
        this._mutationObserver = null
      }
    })

    this._propagateDisabled()
    this._enforceSingleOpen(null)
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "disabled") {
      this._propagateDisabled()
    }
    if (name === "allow-multiple" && newValue === null) {
      this._enforceSingleOpen(null)
    }
    return
  }

  _onMutations(records) {
    let panelsChanged = false
    let openedPanel = null

    for (let index = 0; index < records.length; index = index + 1) {
      const record = records[index]

      if (record.type === "childList" && record.target === this) {
        panelsChanged = true
      } else if (record.type === "attributes" && record.target.parentNode === this) {
        const isPanel = record.target.localName === "mj-disclosure"
        if (isPanel === true && record.target.hasAttribute("open") === true) {
          openedPanel = record.target
        }
      }
    }

    if (panelsChanged === true) {
      this._propagateDisabled()
    }
    if (panelsChanged === true || openedPanel !== null) {
      this._enforceSingleOpen(openedPanel)
    }
    return
  }

  /*
   * Disable every panel while the accordion is disabled and re-enable, when
   * it is enabled again, only the panels it disabled itself. A panel that
   * carries its own `disabled` attribute keeps it.
   */
  _propagateDisabled() {
    const panels = this.panels
    const disabled = this.hasAttribute("disabled")

    for (let index = 0; index < panels.length; index = index + 1) {
      const panel = panels[index]

      if (disabled === true) {
        if (panel.hasAttribute("disabled") === false) {
          panel.setAttribute("disabled", "")
          this._disabledPanels.add(panel)
        }
      } else if (this._disabledPanels.has(panel) === true) {
        panel.removeAttribute("disabled")
        this._disabledPanels.delete(panel)
      }
    }
    return
  }

  /*
   * Unless `allow-multiple` is set, leave one panel open: `keep` when given
   * (the panel that was just opened), otherwise the first open panel.
   */
  _enforceSingleOpen(keep) {
    if (this.hasAttribute("allow-multiple") === true) {
      return
    }

    const panels = this.panels
    let keeper = keep

    for (let index = 0; index < panels.length; index = index + 1) {
      const panel = panels[index]

      if (panel.hasAttribute("open") === true) {
        if (keeper === null) {
          keeper = panel
        } else if (panel !== keeper) {
          /* The attribute, not the property: the panel may not be upgraded yet. */
          panel.removeAttribute("open")
        }
      }
    }
    return
  }

  _onPanelOpened(event) {
    const index = this.panels.indexOf(event.target)
    if (index >= 0) {
      this.emit("mj-accordion-open", { panel: event.target, index: index })
    }
    return
  }

  _onPanelClosed(event) {
    const index = this.panels.indexOf(event.target)
    if (index >= 0) {
      this.emit("mj-accordion-close", { panel: event.target, index: index })
    }
    return
  }

  /*
   * Arrow Up / Down, Home and End move focus between the panel headers. The
   * keys are handled only when they are pressed ON a header of this
   * accordion; anywhere else -- a text field or slider inside a panel, a
   * nested accordion -- they keep their normal meaning.
   */
  _onKeyDown(event) {
    const isNavigationKey =
      event.key === "ArrowDown" || event.key === "ArrowUp" ||
      event.key === "Home" || event.key === "End"
    if (isNavigationKey === false) {
      return
    }

    const origin = event.composedPath()[0]
    const triggers = []
    const panels = this.panels

    for (let index = 0; index < panels.length; index = index + 1) {
      const trigger = panels[index].triggerElement
      const usable = trigger !== null && trigger !== undefined &&
        (panels[index].hasAttribute("disabled") === false || trigger === origin)
      if (usable === true) {
        triggers.push(trigger)
      }
    }

    const activeIndex = triggers.indexOf(origin)
    if (activeIndex < 0) {
      return
    }

    let targetIndex = activeIndex
    if (event.key === "ArrowDown") {
      targetIndex = (activeIndex + 1) % triggers.length
    } else if (event.key === "ArrowUp") {
      targetIndex = (activeIndex - 1 + triggers.length) % triggers.length
    } else if (event.key === "Home") {
      targetIndex = 0
    } else {
      targetIndex = triggers.length - 1
    }

    event.preventDefault()
    triggers[targetIndex].focus()
    return
  }

  get panels() {
    const children = Array.from(this.children)
    const disclosures = children.filter((el) => el.localName === "mj-disclosure")
    return disclosures
  }

  get openPanels() {
    const all = this.panels
    const open = all.filter((p) => p.hasAttribute("open"))
    return open
  }
}
