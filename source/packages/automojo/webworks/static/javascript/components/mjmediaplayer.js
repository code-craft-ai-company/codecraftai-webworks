/*
 * mjmediaplayer.js
 *
 * <mj-media-player> -- accessible video/audio player wrapping a native media
 * element with play/pause, seek, volume, speed, captions, fullscreen, and
 * transcript panel. All controls are keyboard-operable.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host { display: block; }

.player {
  position: relative;
  background: #000;
  border-radius: var(--mj-player-radius, var(--mj-radius-md));
  overflow: hidden;
}

.media-container {
  position: relative;
  width: 100%;
}
:host([type="video"]) .media-container,
:host(:not([type])) .media-container {
  aspect-ratio: var(--_ar, 16/9);
}

video, audio { width: 100%; display: block; }
audio { height: var(--mj-control-height-md); }

.controls {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  background: var(--mj-player-controls-bg, rgba(0,0,0,0.75));
  color: var(--mj-player-controls-color, #fff);
  font-size: var(--mj-font-size-sm);
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease);
}
:host([type="video"]) .controls,
:host(:not([type])) .controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}
.controls.hidden { opacity: 0; pointer-events: none; }

.ctrl-btn {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: var(--mj-space-1);
  border-radius: var(--mj-radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  min-height: 1.5rem;
  flex-shrink: 0;
}
.ctrl-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.ctrl-btn svg { width: 1em; height: 1em; pointer-events: none; }

.seek {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: var(--mj-player-seek-height, 4px);
  border-radius: var(--mj-radius-pill);
  background: rgba(255,255,255,0.3);
  accent-color: var(--mj-player-seek-color, var(--mj-accent));
  cursor: pointer;
}
.seek:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.volume-range {
  width: 4rem;
  -webkit-appearance: none;
  appearance: none;
  height: 3px;
  border-radius: var(--mj-radius-pill);
  background: rgba(255,255,255,0.3);
  accent-color: var(--mj-player-seek-color, var(--mj-accent));
  cursor: pointer;
}

.time { font-size: var(--mj-font-size-xs); white-space: nowrap; flex-shrink: 0; }

.speed-select {
  background: transparent;
  border: none;
  color: inherit;
  font-size: var(--mj-font-size-xs);
  cursor: pointer;
}

.transcript {
  max-height: var(--mj-player-transcript-height, 12rem);
  overflow-y: auto;
  background: var(--mj-player-transcript-bg, var(--mj-surface));
  padding: var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  border-top: 1px solid var(--mj-border);
}
.transcript[hidden] { display: none; }
.cue { padding: var(--mj-space-1) 0; cursor: pointer; }
.cue[aria-current="true"] { color: var(--mj-player-active-cue-color, var(--mj-accent)); font-weight: var(--mj-font-weight-medium); }

.spinner {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.4);
}
.spinner.visible { display: flex; }
.spin-ring {
  width: 2rem; height: 2rem;
  border: 3px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: mj-spin var(--mj-motion-slow) linear infinite;
}
@keyframes mj-spin { to { transform: rotate(360deg); } }

.error-msg {
  display: none;
  padding: var(--mj-space-4);
  color: var(--mj-color-danger);
  text-align: center;
}
.error-msg.visible { display: block; }
`;

export class MjMediaPlayer extends MjElement {
  static tagName = "mj-media-player";
  static styles = STYLES;
  static watched = ["type", "src", "poster", "autoplay", "loop", "muted",
    "controls", "show-transcript", "aspect-ratio", "label", "crossorigin", "preload"];

  constructor() {
    super()
    this._media = null
    this._controlsEl = null
    this._seekEl = null
    this._playBtn = null
    this._timeEl = null
    this._volumeRange = null
    this._muteBtn = null
    this._speedSelect = null
    this._transcriptEl = null
    this._spinnerEl = null
    this._hideTimer = null
  }

  render() {
    const markup = `
      <section part="player" class="player" aria-label="">
        <div class="media-container" part="media-container">
          <div class="media-slot" part="media"></div>
          <div class="spinner" part="loading" aria-hidden="true">
            <div class="spin-ring"></div>
          </div>
          <p class="error-msg" part="error" role="alert"></p>
        </div>
        <div class="controls" part="controls" role="group" aria-label="Media controls">
          <button class="ctrl-btn" part="play-btn" aria-label="Play">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>
          </button>
          <input type="range" class="seek" part="seek"
            aria-label="Seek" min="0" value="0" step="0.1" />
          <span class="time" part="time">0:00 / 0:00</span>
          <button class="ctrl-btn mute-btn" part="volume" aria-label="Mute">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
          </button>
          <input type="range" class="volume-range" aria-label="Volume" min="0" max="1" step="0.05" value="1" />
          <select class="speed-select" part="speed" aria-label="Playback speed"></select>
          <button class="ctrl-btn captions-btn" part="captions-btn" aria-label="Captions" aria-pressed="false" hidden>CC</button>
          <button class="ctrl-btn fs-btn" part="fullscreen-btn" aria-label="Fullscreen" hidden>
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
          </button>
          <slot name="controls-end"></slot>
        </div>
        <div class="transcript" part="transcript" role="log" aria-live="polite" hidden>
          <slot name="transcript"></slot>
        </div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._sectionEl = this.$("section")
    this._mediaSlot = this.$(".media-slot")
    this._spinnerEl = this.$(".spinner")
    this._errorEl = this.$(".error-msg")
    this._controlsEl = this.$(".controls")
    this._playBtn = this.$(".ctrl-btn[part='play-btn']")
    this._seekEl = this.$(".seek")
    this._timeEl = this.$(".time")
    this._muteBtn = this.$(".mute-btn")
    this._volumeRange = this.$(".volume-range")
    this._speedSelect = this.$(".speed-select")
    this._captionsBtn = this.$(".captions-btn")
    this._fsBtn = this.$(".fs-btn")
    this._transcriptEl = this.$(".transcript")

    this._buildMedia()
    this._buildSpeedOptions()
    this._wireControls()
    this._applyAttrs()
    return
  }

  _buildMedia() {
    const type = this.getAttribute("type") || "video"
    const tag = type === "audio" ? "audio" : "video"
    const el = document.createElement(tag)
    el.setAttribute("part", "media")

    const src = this.getAttribute("src") || ""
    if (src.length > 0) { el.setAttribute("src", src) }

    const preload = this.getAttribute("preload") || "metadata"
    el.setAttribute("preload", preload)

    if (tag === "video") {
      const poster = this.getAttribute("poster") || ""
      if (poster.length > 0) { el.setAttribute("poster", poster) }
      this._fsBtn.removeAttribute("hidden")
    }

    const crossorigin = this.getAttribute("crossorigin")
    if (crossorigin !== null) { el.setAttribute("crossorigin", crossorigin) }
    if (this.hasAttribute("loop")) { el.setAttribute("loop", "") }
    if (this.hasAttribute("muted")) { el.muted = true }

    this._mediaSlot.appendChild(el)
    this._media = el

    this.listen(el, "play", () => this._onPlay())
    this.listen(el, "pause", () => this._onPause())
    this.listen(el, "ended", () => this._onEnded())
    this.listen(el, "timeupdate", () => this._onTimeUpdate())
    this.listen(el, "durationchange", () => this._onDurationChange())
    this.listen(el, "volumechange", () => this._onVolumeChange())
    this.listen(el, "waiting", () => this._onWaiting())
    this.listen(el, "playing", () => this._onPlaying())
    this.listen(el, "error", () => this._onMediaError())
    return
  }

  _buildSpeedOptions() {
    const ratesStr = this.getAttribute("playback-rates") || "0.5 0.75 1 1.25 1.5 2"
    const rates = ratesStr.split(/\s+/).map(Number).filter(n => isNaN(n) === false)
    this._speedSelect.innerHTML = ""
    for (let i = 0; i < rates.length; i = i + 1) {
      const opt = document.createElement("option")
      opt.value = String(rates[i])
      opt.textContent = rates[i] + "x"
      if (rates[i] === 1) { opt.selected = true }
      this._speedSelect.appendChild(opt)
    }
    return
  }

  _wireControls() {
    this.listen(this._playBtn, "click", () => this._togglePlay())
    this.listen(this._seekEl, "input", () => this._onSeekInput())
    this.listen(this._muteBtn, "click", () => this._toggleMute())
    this.listen(this._volumeRange, "input", () => {
      if (this._media !== null) { this._media.volume = parseFloat(this._volumeRange.value) }
    })
    this.listen(this._speedSelect, "change", () => {
      const rate = parseFloat(this._speedSelect.value)
      if (this._media !== null) {
        this._media.playbackRate = rate
        this.emit("mj-rate-change", { playbackRate: rate })
      }
    })
    this.listen(this._captionsBtn, "click", () => this._toggleCaptions())
    this.listen(this._fsBtn, "click", () => this._toggleFullscreen())

    this.listen(this._sectionEl, "keydown", (e) => this._onKeyDown(e))

    const type = this.getAttribute("type") || "video"
    if (type === "video") {
      this.listen(this._sectionEl, "pointermove", () => this._showControls())
      this.listen(this._sectionEl, "pointerleave", () => this._scheduleHide())
    }
    return
  }

  _applyAttrs() {
    const label = this.getAttribute("label") || "Media player"
    this._sectionEl.setAttribute("aria-label", label)

    const ar = this.getAttribute("aspect-ratio") || "16/9"
    this.$(".media-container").style.setProperty("--_ar", ar)

    const showTranscript = this.hasAttribute("show-transcript")
    if (showTranscript === true) {
      this._transcriptEl.removeAttribute("hidden")
    }

    const autoplay = this.hasAttribute("autoplay")
    if (autoplay === true) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      if (reduced === true) {
        console.warn("<mj-media-player>: autoplay suppressed due to prefers-reduced-motion.")
      } else if (this._media !== null) {
        this._media.autoplay = true
      }
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._media === null) { return }
    if (name === "label") {
      this._sectionEl.setAttribute("aria-label", newValue || "Media player")
    } else if (name === "src" && newValue !== null) {
      this._media.setAttribute("src", newValue)
      this._media.load()
    }
    return
  }

  _togglePlay() {
    if (this._media === null) { return }
    if (this._media.paused === true) {
      this._media.play()
    } else {
      this._media.pause()
    }
    return
  }

  _onPlay() {
    this._playBtn.setAttribute("aria-label", "Pause")
    this._playBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`
    this.emit("mj-play", { currentTime: this._media.currentTime })
    this._scheduleHide()
    return
  }

  _onPause() {
    this._playBtn.setAttribute("aria-label", "Play")
    this._playBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>`
    this.emit("mj-pause", { currentTime: this._media.currentTime })
    this._showControls()
    return
  }

  _onEnded() {
    this._playBtn.setAttribute("aria-label", "Replay")
    this.emit("mj-ended", {})
    this._showControls()
    return
  }

  _onTimeUpdate() {
    if (this._media === null) { return }
    const ct = this._media.currentTime
    const dur = this._media.duration || 0
    this._seekEl.value = String(ct)
    this._timeEl.textContent = `${this._fmt(ct)} / ${this._fmt(dur)}`
    this._seekEl.setAttribute("aria-valuenow", String(ct.toFixed(1)))
    this._seekEl.setAttribute("aria-valuetext", `${this._fmt(ct)} of ${this._fmt(dur)}`)
    return
  }

  _onDurationChange() {
    if (this._media === null) { return }
    const dur = this._media.duration || 0
    this._seekEl.setAttribute("max", String(dur))
    this._seekEl.setAttribute("aria-valuemax", String(dur))
    this._checkCaptions()
    return
  }

  _onVolumeChange() {
    if (this._media === null) { return }
    this._volumeRange.value = String(this._media.volume)
    const muted = this._media.muted === true || this._media.volume === 0
    this._muteBtn.setAttribute("aria-label", muted ? "Unmute" : "Mute")
    this.emit("mj-volume-change", { volume: this._media.volume, muted: this._media.muted })
    return
  }

  _onWaiting() {
    this._spinnerEl.classList.add("visible")
    announce("Buffering…", "polite")
    return
  }

  _onPlaying() {
    this._spinnerEl.classList.remove("visible")
    return
  }

  _onMediaError() {
    const code = this._media !== null && this._media.error !== null ? this._media.error.code : 0
    const message = `Media error (code ${code})`
    this._errorEl.textContent = message
    this._errorEl.classList.add("visible")
    this.emit("mj-error", { code: code, message: message })
    return
  }

  _onSeekInput() {
    if (this._media === null) { return }
    const prev = this._media.currentTime
    this._media.currentTime = parseFloat(this._seekEl.value)
    this.emit("mj-seek", { currentTime: this._media.currentTime, previousTime: prev })
    return
  }

  _toggleMute() {
    if (this._media === null) { return }
    this._media.muted = this._media.muted === false
    return
  }

  _checkCaptions() {
    if (this._media === null) { return }
    const tracks = this._media.textTracks
    let hasCaptions = false
    for (let i = 0; i < tracks.length; i = i + 1) {
      const kind = tracks[i].kind
      if (kind === "captions" || kind === "subtitles") {
        hasCaptions = true
      }
    }
    if (hasCaptions === true) {
      this._captionsBtn.removeAttribute("hidden")
    }
    return
  }

  _toggleCaptions() {
    if (this._media === null) { return }
    const tracks = this._media.textTracks
    let found = null
    for (let i = 0; i < tracks.length; i = i + 1) {
      const kind = tracks[i].kind
      if (kind === "captions" || kind === "subtitles") {
        found = tracks[i]
        break
      }
    }
    if (found === null) { return }

    const wasShowing = found.mode === "showing"
    found.mode = wasShowing ? "hidden" : "showing"
    this._captionsBtn.setAttribute("aria-pressed", wasShowing ? "false" : "true")
    this.emit("mj-captions-change", { track: wasShowing ? null : found.label })
    return
  }

  _toggleFullscreen() {
    const container = this.$(".media-container")
    if (document.fullscreenElement !== null) {
      document.exitFullscreen()
    } else {
      container.requestFullscreen().catch((err) => {
        console.warn("<mj-media-player>: fullscreen request rejected.", err)
        this._fsBtn.setAttribute("hidden", "")
      })
    }
    return
  }

  _onKeyDown(event) {
    if (this._media === null) { return }
    const key = event.key
    const actions = {
      " ": () => this._togglePlay(),
      "k": () => this._togglePlay(),
      "K": () => this._togglePlay(),
      "ArrowLeft": () => { this._media.currentTime = Math.max(0, this._media.currentTime - 5) },
      "ArrowRight": () => { this._media.currentTime = Math.min(this._media.duration || 0, this._media.currentTime + 5) },
      "ArrowUp": () => { this._media.volume = Math.min(1, this._media.volume + 0.1) },
      "ArrowDown": () => { this._media.volume = Math.max(0, this._media.volume - 0.1) },
      "m": () => this._toggleMute(),
      "M": () => this._toggleMute(),
      "f": () => this._toggleFullscreen(),
      "F": () => this._toggleFullscreen(),
      "c": () => this._toggleCaptions(),
      "C": () => this._toggleCaptions(),
      "Home": () => { this._media.currentTime = 0 },
      "End": () => { this._media.currentTime = this._media.duration || 0 }
    }
    const digit = /^[0-9]$/.test(key)
    if (digit === true) {
      const pct = parseInt(key, 10) / 10
      this._media.currentTime = (this._media.duration || 0) * pct
      event.preventDefault()
      return
    }
    if (actions[key] !== undefined) {
      event.preventDefault()
      actions[key]()
    }
    return
  }

  _showControls() {
    this._controlsEl.classList.remove("hidden")
    if (this._hideTimer !== null) {
      clearTimeout(this._hideTimer)
      this._hideTimer = null
    }
    return
  }

  _scheduleHide() {
    if (this._media === null || this._media.paused === true) { return }
    if (this._hideTimer !== null) { clearTimeout(this._hideTimer) }
    this._hideTimer = setTimeout(() => {
      this._controlsEl.classList.add("hidden")
      this._hideTimer = null
    }, 3000)
    return
  }

  _fmt(seconds) {
    const s = Math.floor(seconds) || 0
    const m = Math.floor(s / 60)
    const sec = s % 60
    const formatted = `${m}:${sec < 10 ? "0" : ""}${sec}`
    return formatted
  }

  onDisconnected() {
    if (this._hideTimer !== null) {
      clearTimeout(this._hideTimer)
      this._hideTimer = null
    }
    return
  }

  /* ----- scriptable API ----- */

  get mediaElement() { return this._media }
  get paused() { return this._media === null ? true : this._media.paused }
  get duration() { return this._media === null ? 0 : this._media.duration }
  get textTracks() { return this._media === null ? null : this._media.textTracks }

  get currentTime() { return this._media === null ? 0 : this._media.currentTime }
  set currentTime(v) { if (this._media !== null) { this._media.currentTime = v } }

  get volume() { return this._media === null ? 1 : this._media.volume }
  set volume(v) { if (this._media !== null) { this._media.volume = v } }

  get muted() { return this._media === null ? false : this._media.muted }
  set muted(v) { if (this._media !== null) { this._media.muted = v } }

  get playbackRate() { return this._media === null ? 1 : this._media.playbackRate }
  set playbackRate(v) { if (this._media !== null) { this._media.playbackRate = v } }
}
