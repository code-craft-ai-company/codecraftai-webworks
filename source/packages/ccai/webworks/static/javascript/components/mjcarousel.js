/*
 * mjcarousel.js
 *
 * <mj-carousel> -- displays a sequence of slides with prev/next controls and
 * picker tabs. Follows the WAI-ARIA APG carousel pattern.
 *
 * Slides are the carousel's element children -- any element works: a <div>,
 * an <article>, an <mj-card>, or the conventional <mj-carousel-slide> tag
 * (which is a plain element; no separate component is needed). The carousel
 * sizes every slide to the full width of the viewport and manages on it:
 *   aria-hidden            "false" on the current slide, "true" on the others
 *   role / aria-roledescription / aria-label
 *                          a labelled "slide" group, unless the author set
 *                          those attributes
 * Slides that are not current are clipped and `visibility: hidden`, so their
 * content is neither focusable nor read.
 *
 * Auto-rotation has ONE state, `playing`. Hovering or focusing the carousel
 * suspends the timer without changing that state; `mj-carousel-play` and
 * `mj-carousel-pause` fire only when `playing` itself changes.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const DEFAULT_LABEL_KEY = "mj.carousel.label";
const DEFAULT_PREV_LABEL_KEY = "mj.carousel.previousSlide";
const DEFAULT_NEXT_LABEL_KEY = "mj.carousel.nextSlide";
const DEFAULT_INTERVAL_MS = 5000;
const MIN_INTERVAL_MS = 1000;

const STYLES = `
:host {
  display: block;
  position: relative;
}

.root {
  position: relative;
}

.viewport {
  overflow: hidden;
}

/*
 * slide / none: the slides sit side by side and the track is shifted by one
 * viewport width per slide. The shift follows the inline direction.
 */
.slides-container {
  display: flex;
  align-items: stretch;
  transform: translateX(calc(var(--mj-carousel-index, 0) * -100%));
  transition: transform var(--mj-carousel-slide-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}

.slides-container:dir(rtl) {
  transform: translateX(calc(var(--mj-carousel-index, 0) * 100%));
}

::slotted(*) {
  flex: 0 0 100%;
  box-sizing: border-box;
  min-inline-size: 0;
  max-inline-size: 100%;
}

/* A slide leaving view stays visible until the track has moved on. */
::slotted([aria-hidden="true"]) {
  visibility: hidden;
  transition: visibility 0s linear var(--mj-carousel-slide-duration, var(--mj-motion-medium));
}

::slotted([aria-hidden="false"]) {
  visibility: visible;
  transition: visibility 0s linear 0s;
}

/* fade: the slides are stacked in one cell and cross-fade. */
:host([transition="fade"]) .slides-container {
  display: grid;
  transform: none;
  transition: none;
}

:host([transition="fade"]) ::slotted(*) {
  grid-area: 1 / 1;
  opacity: 0;
  transition:
    opacity var(--mj-carousel-slide-duration, var(--mj-motion-medium)) var(--mj-motion-ease),
    visibility 0s linear var(--mj-carousel-slide-duration, var(--mj-motion-medium));
}

:host([transition="fade"]) ::slotted([aria-hidden="false"]) {
  opacity: 1;
  transition:
    opacity var(--mj-carousel-slide-duration, var(--mj-motion-medium)) var(--mj-motion-ease),
    visibility 0s linear 0s;
}

:host([transition="none"]) .slides-container,
:host([transition="none"]) ::slotted(*) {
  transition: none;
}

@media (prefers-reduced-motion: reduce) {
  .slides-container,
  ::slotted(*) {
    transition: none !important;
  }
}

.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  padding-block: var(--mj-space-3);
}

.control-btn {
  flex: 0 0 auto;
  width: var(--mj-carousel-control-size, 2.5rem);
  height: var(--mj-carousel-control-size, 2.5rem);
  padding: 0;
  border-radius: var(--mj-radius-circle);
  border: 1px solid var(--mj-border-strong);
  background: var(--mj-carousel-control-bg, var(--mj-surface));
  color: var(--mj-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font: inherit;
  font-size: var(--mj-font-size-md);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease);
}

.control-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.control-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/*
 * The chevrons point along the inline axis. U+2039 / U+203A are
 * Bidi_Mirrored, so in an RTL context the text engine already draws them
 * mirrored (the previous button, at the inline start on the right, points
 * right); a transform here would flip them back to pointing inward.
 */

.autoplay-btn svg {
  width: 1rem;
  height: 1rem;
  fill: currentColor;
}

.autoplay-btn .icon-play,
.autoplay-btn[data-playing="true"] .icon-pause {
  display: block;
}

.autoplay-btn .icon-pause,
.autoplay-btn[data-playing="true"] .icon-play {
  display: none;
}

.picker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--mj-carousel-picker-gap, var(--mj-space-2));
  flex: 1;
}

/*
 * The button is the pointer target (at least 24px); the dot drawn inside it
 * keeps the small visual size.
 */
.picker-item {
  inline-size: max(1.5rem, var(--mj-carousel-picker-size, 0.5rem));
  block-size: max(1.5rem, var(--mj-carousel-picker-size, 0.5rem));
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--mj-radius-circle);
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.picker-item::before {
  content: "";
  inline-size: var(--mj-carousel-picker-size, 0.5rem);
  block-size: var(--mj-carousel-picker-size, 0.5rem);
  border-radius: var(--mj-radius-circle);
  background: var(--mj-border-strong);
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              transform var(--mj-motion-fast) var(--mj-motion-ease);
}

.picker-item[aria-selected="true"]::before {
  background: var(--mj-carousel-picker-active-color, var(--mj-accent));
  transform: scale(1.4);
}

.picker-item:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([show-controls="false"]) .prev-btn,
:host([show-controls="false"]) .next-btn { display: none; }

:host([show-picker="false"]) .picker { display: none; }
`;

export class MjCarousel extends MjElement {
  static tagName = "mj-carousel";
  static styles = STYLES;
  static watched = [
    "current-index", "autoplay", "autoplay-interval", "loop",
    "show-picker", "show-controls", "label", "transition",
    "prev-label", "next-label"
  ];

  constructor() {
    super()
    this._pickerId = nextId("mj-carousel-picker")
    this._root = null
    this._slidesContainer = null
    this._controls = null
    this._prevBtn = null
    this._nextBtn = null
    this._picker = null
    this._autoplayBtn = null
    this._mutationObserver = null

    /* The index of the slide on display, always inside the slide list. */
    this._index = 0

    /* Auto-rotation: the one public state and what temporarily suspends it. */
    this._playing = false
    this._hovering = false
    this._focusWithin = false
    this._autoplayTimer = null

    /* The `autoplay` attribute state already acted on. */
    this._autoplayApplied = false

    /* What the carousel wrote on each slide, so only that is updated or removed. */
    this._slideRecords = new WeakMap()
  }

  render() {
    const markup = html`
      <section class="root" part="root" role="region">
        <div class="viewport">
          <div class="slides-container" part="slides-container" aria-live="polite">
            <slot></slot>
          </div>
        </div>
        <div class="controls" part="controls">
          <button type="button" class="control-btn prev-btn" part="prev-button">
            <span class="chevron" aria-hidden="true">&#8249;</span>
          </button>
          <div class="picker" part="picker" role="tablist" id="${this._pickerId}"></div>
          <button type="button" class="control-btn autoplay-btn" part="autoplay-button" hidden>
            <svg class="icon-pause" aria-hidden="true" viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"></rect><rect x="9" y="2" width="4" height="12"></rect></svg>
            <svg class="icon-play" aria-hidden="true" viewBox="0 0 16 16"><path d="M4 2 L14 8 L4 14 Z"></path></svg>
          </button>
          <button type="button" class="control-btn next-btn" part="next-button">
            <span class="chevron" aria-hidden="true">&#8250;</span>
          </button>
        </div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._root = this.$(".root")
    this._slidesContainer = this.$(".slides-container")
    this._controls = this.$(".controls")
    this._prevBtn = this.$(".prev-btn")
    this._nextBtn = this.$(".next-btn")
    this._picker = this.$(".picker")
    this._autoplayBtn = this.$(".autoplay-btn")

    this.listen(this._prevBtn, "click", () => this._navigate(-1, "user"))
    this.listen(this._nextBtn, "click", () => this._navigate(1, "user"))
    this.listen(this._autoplayBtn, "click", this._onAutoplayBtnClick.bind(this))
    this.listen(this._picker, "click", this._onPickerClick.bind(this))
    this.listen(this._picker, "keydown", this._onPickerKeyDown.bind(this))
    this.listen(this, "mouseenter", () => this._setSuspended("hover", true))
    this.listen(this, "mouseleave", () => this._setSuspended("hover", false))
    this.listen(this, "focusin", () => this._setSuspended("focus", true))
    this.listen(this, "focusout", this._onFocusOut.bind(this))

    this._syncLabels()
    this._syncSlides()
    this._syncAutoplayAttribute()
    return
  }

  onConnected() {
    this._mutationObserver = new MutationObserver((records) => {
      this._onChildrenChanged(records)
    })
    this._mutationObserver.observe(this, { childList: true })

    this.onTeardown(() => {
      this._stopTimer()
      this._hovering = false
      this._focusWithin = false
      if (this._mutationObserver !== null) {
        this._mutationObserver.disconnect()
        this._mutationObserver = null
      }
    })

    /* A re-connect starts the timer again when rotation was on. */
    this._syncTimer()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._slidesContainer === undefined || this._slidesContainer === null) {
      return
    }

    if (name === "current-index" || name === "loop") {
      this._syncSlides()
      this._syncTimer()
    } else if (name === "autoplay") {
      this._syncAutoplayAttribute()
    } else if (name === "autoplay-interval") {
      this._stopTimer()
      this._syncTimer()
    } else if (name === "label" || name === "prev-label" || name === "next-label") {
      this._syncLabels()
    }
    return
  }

  /* ----- slides ----- */

  /* The slides: every element child that is not assigned to a named slot. */
  _getSlides() {
    const children = Array.from(this.children)
    const slides = children.filter((element) => element.hasAttribute("slot") === false)
    return slides
  }

  /* The index `current-index` asks for, limited to the slides that exist. */
  _requestedIndex(slideCount) {
    const parsed = parseInt(this.getAttribute("current-index") || "0", 10)
    let index = Number.isNaN(parsed) === true ? 0 : parsed

    if (slideCount === 0) {
      index = 0
    } else {
      index = Math.max(0, Math.min(slideCount - 1, index))
    }

    return index
  }

  _onChildrenChanged(records) {
    /* Take the carousel's attributes back off slides that were removed. */
    for (let index = 0; index < records.length; index = index + 1) {
      const removed = records[index].removedNodes
      for (let nodeIndex = 0; nodeIndex < removed.length; nodeIndex = nodeIndex + 1) {
        const node = removed[nodeIndex]
        if (node.nodeType === Node.ELEMENT_NODE && node.parentNode !== this) {
          this._releaseSlide(node)
        }
      }
    }

    this._syncSlides()
    this._syncTimer()
    return
  }

  /*
   * Give a slide its group semantics and position label. Attributes the
   * author set are left alone; only what the carousel wrote is updated.
   */
  _describeSlide(slide, position, total) {
    let record = this._slideRecords.get(slide)
    if (record === undefined) {
      record = { role: false, roleDescription: false, label: null }
      this._slideRecords.set(slide, record)
    }

    if (slide.hasAttribute("role") === false) {
      slide.setAttribute("role", "group")
      record.role = true
    }

    if (slide.hasAttribute("aria-roledescription") === false) {
      slide.setAttribute("aria-roledescription", t("mj.carousel.slideRoleDescription"))
      record.roleDescription = true
    }

    const authorLabelled = slide.hasAttribute("aria-labelledby") === true ||
      (slide.hasAttribute("aria-label") === true && slide.getAttribute("aria-label") !== record.label)
    if (authorLabelled === false) {
      record.label = t("mj.carousel.slideLabel", { n: position, total: total })
      slide.setAttribute("aria-label", record.label)
    }
    return
  }

  _releaseSlide(slide) {
    const record = this._slideRecords.get(slide)
    if (record === undefined) {
      return
    }

    slide.removeAttribute("aria-hidden")
    if (record.role === true) {
      slide.removeAttribute("role")
    }
    if (record.roleDescription === true) {
      slide.removeAttribute("aria-roledescription")
    }
    if (record.label !== null && slide.getAttribute("aria-label") === record.label) {
      slide.removeAttribute("aria-label")
    }
    this._slideRecords.delete(slide)
    return
  }

  /*
   * Bring slides, picker and controls in line with `current-index` and the
   * current children. Idempotent; emits nothing.
   */
  _syncSlides() {
    if (this._slidesContainer === null || this._slidesContainer === undefined) {
      return
    }

    const slides = this._getSlides()
    const total = slides.length
    this._index = this._requestedIndex(total)

    /*
     * Write an out-of-range index back, so the attribute always names the
     * slide on display. Not while the document is still being parsed: more
     * slides may be on their way.
     */
    const attribute = this.getAttribute("current-index")
    const outOfRange = attribute !== null && attribute !== String(this._index)
    if (outOfRange === true && total > 0 && document.readyState !== "loading") {
      this.setAttribute("current-index", String(this._index))
    }

    for (let index = 0; index < total; index = index + 1) {
      const slide = slides[index]
      slide.setAttribute("aria-hidden", index === this._index ? "false" : "true")
      this._describeSlide(slide, index + 1, total)
    }

    this._slidesContainer.style.setProperty("--mj-carousel-index", String(this._index))

    this._syncPicker(total)

    const loop = this.hasAttribute("loop")
    this._prevBtn.disabled = total === 0 || (loop === false && this._index === 0)
    this._nextBtn.disabled = total === 0 || (loop === false && this._index === total - 1)

    /* Nothing to navigate with a single slide (or none). */
    this._controls.hidden = total <= 1
    return
  }

  /* ----- picker ----- */

  /*
   * One tab per slide with a roving tabindex: only the selected tab is in
   * the tab order. The tabs are rebuilt only when the slide count changes,
   * so a focused tab keeps focus across ordinary updates.
   */
  _syncPicker(total) {
    let tabs = Array.from(this._picker.children)

    if (tabs.length !== total) {
      this._picker.textContent = ""
      for (let index = 0; index < total; index = index + 1) {
        const tab = document.createElement("button")
        tab.type = "button"
        tab.className = "picker-item"
        tab.setAttribute("part", "picker-item")
        tab.setAttribute("role", "tab")
        this._picker.appendChild(tab)
      }
      tabs = Array.from(this._picker.children)
    }

    for (let index = 0; index < tabs.length; index = index + 1) {
      const selected = index === this._index
      tabs[index].setAttribute("aria-label", t("mj.carousel.slideLabel", { n: index + 1, total: total }))
      tabs[index].setAttribute("aria-selected", selected === true ? "true" : "false")
      tabs[index].setAttribute("tabindex", selected === true ? "0" : "-1")
    }
    return
  }

  _onPickerClick(event) {
    const tabs = Array.from(this._picker.children)
    const index = tabs.indexOf(event.target)
    if (index >= 0) {
      this._goTo(index, "user")
    }
    return
  }

  /*
   * Arrow Left / Right, Home and End act only while a picker tab has focus,
   * per the APG tabs pattern; in slide content and on the other controls
   * the keys keep their normal meaning. Focus follows the selection. The
   * arrows follow the inline direction.
   */
  _onPickerKeyDown(event) {
    const tabs = Array.from(this._picker.children)
    const current = tabs.indexOf(event.target)
    if (current < 0 || tabs.length === 0) {
      return
    }

    const rtl = window.getComputedStyle(this).direction === "rtl"
    const last = tabs.length - 1
    let target = null

    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      const forward = (event.key === "ArrowRight") !== rtl
      target = current + (forward === true ? 1 : -1)
      if (target > last) {
        target = 0
      } else if (target < 0) {
        target = last
      }
    } else if (event.key === "Home") {
      target = 0
    } else if (event.key === "End") {
      target = last
    }

    if (target !== null) {
      event.preventDefault()
      this._goTo(target, "user")
      const selected = this._picker.children[this._index]
      if (selected !== undefined) {
        selected.focus()
      }
    }
    return
  }

  /* ----- navigation ----- */

  _navigate(delta, trigger) {
    const total = this._getSlides().length
    if (total === 0) {
      return
    }

    let next = this._index + delta
    if (this.hasAttribute("loop") === true) {
      next = ((next % total) + total) % total
    } else {
      next = Math.max(0, Math.min(total - 1, next))
    }

    this._goTo(next, trigger)
    return
  }

  /*
   * Show slide `index` in response to the user or the rotation timer.
   * `mj-carousel-change` can veto the move; `mj-carousel-changed` follows.
   */
  _goTo(index, trigger) {
    const total = this._getSlides().length
    if (total === 0 || index < 0 || index >= total || index === this._index) {
      return
    }

    const previous = this._index
    const proceed = this.emit("mj-carousel-change", {
      index: index,
      previousIndex: previous,
      trigger: trigger || "user"
    }, { cancelable: true })

    if (proceed === false) {
      return
    }

    this.setAttribute("current-index", String(index))
    this._syncSlides()
    this._syncTimer()

    this.emit("mj-carousel-changed", { index: index, previousIndex: previous })
    return
  }

  /* ----- labels ----- */

  _syncLabels() {
    const label = this.getAttribute("label")
    const prevLabel = this.getAttribute("prev-label")
    const nextLabel = this.getAttribute("next-label")

    this._root.setAttribute("aria-roledescription", t("mj.carousel.roleDescription"))
    this._root.setAttribute("aria-label", label !== null && label.length > 0 ? label : t(DEFAULT_LABEL_KEY))
    this._picker.setAttribute("aria-label", t("mj.carousel.chooseSlide"))
    this._prevBtn.setAttribute("aria-label", prevLabel !== null && prevLabel.length > 0 ? prevLabel : t(DEFAULT_PREV_LABEL_KEY))
    this._nextBtn.setAttribute("aria-label", nextLabel !== null && nextLabel.length > 0 ? nextLabel : t(DEFAULT_NEXT_LABEL_KEY))
    return
  }

  /* ----- auto-rotation ----- */

  /*
   * React to the `autoplay` attribute appearing or going away. Rotation
   * starts with it, except for users who asked for reduced motion: they get
   * the control but have to start the rotation themselves.
   */
  _syncAutoplayAttribute() {
    const enabled = this.hasAttribute("autoplay")

    if (enabled !== this._autoplayApplied) {
      this._autoplayApplied = enabled
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      this._setPlaying(enabled === true && reducedMotion === false)
    }

    this._syncAutoplayControl()
    this._syncTimer()
    return
  }

  /* The one place `playing` changes; announces the change exactly once. */
  _setPlaying(playing) {
    if (playing === this._playing) {
      return
    }

    this._playing = playing
    this._syncAutoplayControl()
    this._syncTimer()
    this.emit(playing === true ? "mj-carousel-play" : "mj-carousel-pause", {})
    return
  }

  _syncAutoplayControl() {
    this._autoplayBtn.hidden = this.hasAttribute("autoplay") === false
    this._autoplayBtn.setAttribute("data-playing", this._playing === true ? "true" : "false")
    this._autoplayBtn.setAttribute(
      "aria-label",
      this._playing === true ? t("mj.carousel.stopAutoRotation") : t("mj.carousel.startAutoRotation")
    )
    return
  }

  _intervalMs() {
    const parsed = parseInt(this.getAttribute("autoplay-interval") || "", 10)
    const interval = Number.isNaN(parsed) === true ? DEFAULT_INTERVAL_MS : Math.max(MIN_INTERVAL_MS, parsed)
    return interval
  }

  _stopTimer() {
    if (this._autoplayTimer !== null) {
      window.clearInterval(this._autoplayTimer)
      this._autoplayTimer = null
    }
    return
  }

  /*
   * Run the rotation timer exactly while rotation is on, nothing suspends
   * it and there is a slide to advance to. Slide changes are announced
   * (aria-live) only while the timer is not running.
   */
  _syncTimer() {
    if (this._slidesContainer === null || this._slidesContainer === undefined) {
      return
    }

    const total = this._getSlides().length
    const shouldRun =
      this._playing === true && this.isConnected === true &&
      this._hovering === false && this._focusWithin === false && total > 1

    if (shouldRun === true && this._autoplayTimer === null) {
      this._autoplayTimer = window.setInterval(() => {
        this._advance()
      }, this._intervalMs())
    } else if (shouldRun === false) {
      this._stopTimer()
    }

    this._slidesContainer.setAttribute("aria-live", this._autoplayTimer !== null ? "off" : "polite")
    return
  }

  /* One step of the rotation. A carousel that does not loop stops at its end. */
  _advance() {
    const total = this._getSlides().length
    const atEnd = this._index >= total - 1

    if (atEnd === true && this.hasAttribute("loop") === false) {
      this._setPlaying(false)
    } else {
      this._navigate(1, "auto")
    }
    return
  }

  _setSuspended(reason, suspended) {
    if (reason === "hover") {
      this._hovering = suspended
    } else {
      this._focusWithin = suspended
    }
    this._syncTimer()
    return
  }

  _onFocusOut(event) {
    const next = event.relatedTarget
    const stillInside = next !== null && next !== undefined &&
      (this.contains(next) === true || this.shadowRoot.contains(next) === true)
    this._setSuspended("focus", stillInside)
    return
  }

  _onAutoplayBtnClick() {
    this.playing = this._playing === false
    return
  }

  /* ----- public API ----- */

  get slides() {
    return this._getSlides()
  }

  /* Zero-based index of the slide on display. */
  get currentIndex() {
    return this._index
  }

  /* True while auto-rotation is switched on (it may be suspended by hover or focus). */
  get playing() {
    return this._playing
  }

  set playing(value) {
    const playing = Boolean(value)

    if (playing === true && this._slidesContainer !== null && this._slidesContainer !== undefined) {
      /* Starting at the end of a carousel that does not loop begins again. */
      const total = this._getSlides().length
      if (this.hasAttribute("loop") === false && total > 1 && this._index >= total - 1) {
        this._goTo(0, "auto")
      }
    }

    this._setPlaying(playing)
    return
  }
}
