/*
 * mjcarousel.js
 *
 * <mj-carousel> -- displays a sequence of slides with prev/next controls and
 * picker tabs. Follows the WAI-ARIA APG carousel pattern.
 */

import { MjElement, nextId } from "../core/mjelement.js";

const STYLES = `
:host {
  display: block;
  position: relative;
}

.root {
  position: relative;
  overflow: hidden;
}

.slides-container {
  display: flex;
  transition: transform var(--mj-carousel-slide-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}

:host([transition="fade"]) .slides-container {
  display: block;
  position: relative;
}

:host([transition="none"]) .slides-container {
  transition: none;
}

@media (prefers-reduced-motion: reduce) {
  .slides-container { transition: none; }
}

.controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  padding-block: var(--mj-space-3);
}

.control-btn {
  width: var(--mj-carousel-control-size, 2.5rem);
  height: var(--mj-carousel-control-size, 2.5rem);
  border-radius: var(--mj-radius-circle);
  border: 1px solid var(--mj-border-strong);
  background: var(--mj-carousel-control-bg, var(--mj-surface));
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
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

.picker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-carousel-picker-gap, var(--mj-space-2));
  flex: 1;
}

.picker-item {
  width: var(--mj-carousel-picker-size, 0.5rem);
  height: var(--mj-carousel-picker-size, 0.5rem);
  border-radius: var(--mj-radius-circle);
  border: none;
  background: var(--mj-border-strong);
  cursor: pointer;
  padding: 0;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              transform var(--mj-motion-fast) var(--mj-motion-ease);
}

.picker-item[aria-selected="true"] {
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
    "show-picker", "show-controls", "label", "transition"
  ];

  constructor() {
    super()
    this._autoplayTimer = null
    this._playing = false
    this._transitioning = false
    this._userStopped = false
    this._mutationObserver = null
    this._pickerId = nextId("mj-carousel-picker")
  }

  render() {
    const label = this.getAttribute("label") || "Carousel"
    const markup = `
      <section class="root" part="root" role="region" aria-label="${label}" aria-roledescription="carousel">
        <div class="slides-container" part="slides-container" aria-live="off">
          <slot></slot>
        </div>
        <div class="controls" part="controls">
          <button class="control-btn prev-btn" part="prev-button" aria-label="Previous slide">&#8249;</button>
          <div class="picker" part="picker" role="tablist" aria-label="Choose slide" id="${this._pickerId}"></div>
          <button class="control-btn autoplay-btn" part="autoplay-button" aria-label="Start auto-rotation" aria-pressed="false" style="display:none"></button>
          <button class="control-btn next-btn" part="next-button" aria-label="Next slide">&#8250;</button>
        </div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._slidesContainer = this.$(".slides-container")
    this._prevBtn = this.$(".prev-btn")
    this._nextBtn = this.$(".next-btn")
    this._picker = this.$(".picker")
    this._autoplayBtn = this.$(".autoplay-btn")

    this.listen(this._prevBtn, "click", () => this._navigate(-1, "user"))
    this.listen(this._nextBtn, "click", () => this._navigate(1, "user"))
    this.listen(this._autoplayBtn, "click", this._onAutoplayBtnClick.bind(this))
    this.listen(this, "mouseenter", this._pauseAutoplay.bind(this))
    this.listen(this, "mouseleave", this._resumeAutoplay.bind(this))
    this.listen(this, "focusin", this._pauseAutoplay.bind(this))
    this.listen(this, "focusout", this._resumeAutoplay.bind(this))
    this.listen(this, "keydown", this._onKeyDown.bind(this))

    this._buildPicker()
    this._updateSlides()

    if (this.hasAttribute("autoplay")) {
      this._autoplayBtn.style.display = ""
      this._autoplayBtn.setAttribute("aria-label", "Stop auto-rotation")
      this._autoplayBtn.setAttribute("aria-pressed", "true")
      this._startAutoplay()
    }
    return
  }

  onConnected() {
    this._mutationObserver = new MutationObserver(() => {
      this._buildPicker()
      this._updateSlides()
    })
    this._mutationObserver.observe(this, { childList: true })
    return
  }

  onDisconnected() {
    this._stopAutoplay()
    if (this._mutationObserver !== null) {
      this._mutationObserver.disconnect()
      this._mutationObserver = null
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._slidesContainer === undefined) {
      return
    }
    if (name === "current-index") {
      this._updateSlides()
    } else if (name === "autoplay") {
      if (newValue !== null) {
        this._autoplayBtn.style.display = ""
        this._startAutoplay()
      } else {
        this._stopAutoplay()
        this._autoplayBtn.style.display = "none"
      }
    } else if (name === "label") {
      const root = this.$(".root")
      if (root !== null) {
        root.setAttribute("aria-label", newValue || "Carousel")
      }
    }
    return
  }

  _getSlides() {
    return Array.from(this.children).filter((el) => el.tagName.toLowerCase() === "mj-carousel-slide")
  }

  _buildPicker() {
    if (this._picker === null) {
      return
    }
    const slides = this._getSlides()
    this._picker.innerHTML = ""
    for (let i = 0; i < slides.length; i = i + 1) {
      const btn = document.createElement("button")
      btn.className = "picker-item"
      btn.setAttribute("part", "picker-item")
      btn.setAttribute("role", "tab")
      btn.setAttribute("aria-label", `Slide ${i + 1} of ${slides.length}`)
      const idx = i
      btn.addEventListener("click", () => {
        this._goTo(idx, "user")
      })
      this._picker.appendChild(btn)
    }
    return
  }

  _updateSlides() {
    const slides = this._getSlides()
    const currentIndex = parseInt(this.getAttribute("current-index") || "0", 10)
    const safeIndex = Math.max(0, Math.min(slides.length - 1, currentIndex))

    for (let i = 0; i < slides.length; i = i + 1) {
      const slide = slides[i]
      const isActive = i === safeIndex
      slide.setAttribute("aria-hidden", isActive === true ? "false" : "true")
      slide.style.display = isActive === true ? "" : "none"
    }

    const pickerItems = this._picker !== null ? Array.from(this._picker.querySelectorAll(".picker-item")) : []
    for (let i = 0; i < pickerItems.length; i = i + 1) {
      pickerItems[i].setAttribute("aria-selected", i === safeIndex ? "true" : "false")
    }

    const loop = this.hasAttribute("loop")
    if (this._prevBtn !== null) {
      this._prevBtn.disabled = loop === false && safeIndex === 0
    }
    if (this._nextBtn !== null) {
      this._nextBtn.disabled = loop === false && safeIndex === slides.length - 1
    }
    return
  }

  _navigate(delta, trigger) {
    const slides = this._getSlides()
    if (slides.length === 0) {
      return
    }
    const current = parseInt(this.getAttribute("current-index") || "0", 10)
    const loop = this.hasAttribute("loop")
    let next = current + delta

    if (loop === true) {
      next = ((next % slides.length) + slides.length) % slides.length
    } else {
      next = Math.max(0, Math.min(slides.length - 1, next))
    }

    this._goTo(next, trigger)
    return
  }

  _goTo(index, trigger) {
    if (this._transitioning === true) {
      return
    }
    const current = parseInt(this.getAttribute("current-index") || "0", 10)
    if (index === current) {
      return
    }

    const proceed = this.emit("mj-carousel-change", {
      index: index,
      previousIndex: current,
      trigger: trigger || "user"
    }, { cancelable: true })

    if (proceed === false) {
      return
    }

    if (trigger === "user" && this._slidesContainer !== null) {
      this._slidesContainer.setAttribute("aria-live", "polite")
    }

    this.setAttribute("current-index", String(index))
    this._updateSlides()

    this.emit("mj-carousel-changed", { index: index, previousIndex: current })

    if (this._slidesContainer !== null) {
      setTimeout(() => {
        if (this._slidesContainer !== null) {
          this._slidesContainer.setAttribute("aria-live", "off")
        }
      }, 1000)
    }
    return
  }

  _startAutoplay() {
    this._stopAutoplay()
    const interval = parseInt(this.getAttribute("autoplay-interval") || "5000", 10)
    const safeInterval = Math.max(1000, interval)
    this._autoplayTimer = setInterval(() => {
      this._navigate(1, "auto")
    }, safeInterval)
    this._playing = true
    this.emit("mj-carousel-play", {})
    return
  }

  _stopAutoplay() {
    if (this._autoplayTimer !== null) {
      clearInterval(this._autoplayTimer)
      this._autoplayTimer = null
    }
    if (this._playing === true) {
      this._playing = false
      this.emit("mj-carousel-pause", {})
    }
    return
  }

  _pauseAutoplay() {
    if (this._autoplayTimer !== null) {
      clearInterval(this._autoplayTimer)
      this._autoplayTimer = null
    }
    return
  }

  _resumeAutoplay() {
    if (this._userStopped === true) {
      return
    }
    if (this.hasAttribute("autoplay") && this._autoplayTimer === null) {
      this._startAutoplay()
    }
    return
  }

  _onAutoplayBtnClick() {
    if (this._playing === true) {
      this._stopAutoplay()
      this._userStopped = true
      this._autoplayBtn.setAttribute("aria-label", "Start auto-rotation")
      this._autoplayBtn.setAttribute("aria-pressed", "false")
    } else {
      this._userStopped = false
      this._startAutoplay()
      this._autoplayBtn.setAttribute("aria-label", "Stop auto-rotation")
      this._autoplayBtn.setAttribute("aria-pressed", "true")
    }
    return
  }

  _onKeyDown(event) {
    const slides = this._getSlides()
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault()
      this._navigate(-1, "user")
    } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault()
      this._navigate(1, "user")
    } else if (event.key === "Home") {
      event.preventDefault()
      this._goTo(0, "user")
    } else if (event.key === "End") {
      event.preventDefault()
      this._goTo(slides.length - 1, "user")
    }
    return
  }

  get slides() {
    return this._getSlides()
  }

  get playing() {
    return this._playing
  }

  set playing(value) {
    if (value === true) {
      this._userStopped = false
      this._startAutoplay()
    } else {
      this._userStopped = true
      this._stopAutoplay()
    }
    return
  }
}
