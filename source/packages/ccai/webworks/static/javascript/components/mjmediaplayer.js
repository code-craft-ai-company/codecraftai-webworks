/*
 * mjmediaplayer.js
 *
 * <mj-media-player> -- accessible video/audio player wrapping a native media
 * element with play/pause, seek, volume, speed, captions, fullscreen, and
 * transcript panel. All controls are keyboard-operable.
 *
 * Sources and captions
 *   `src` sets a single source. Alternate sources and text tracks are
 *   authored as light-DOM children:
 *
 *     <mj-media-player label="Interview">
 *       <source src="talk.webm" type="video/webm">
 *       <source src="talk.mp4" type="video/mp4">
 *       <track kind="captions" src="talk.en.vtt" srclang="en" label="English" default>
 *     </mj-media-player>
 *
 *   The native media element lives in the shadow root, so the children are
 *   mirrored into it (fresh elements carrying only the known attributes) on
 *   connect and whenever the children change. The originals stay in the
 *   light DOM, so frameworks and reconnects keep working.
 *
 * Keyboard
 *   Shortcuts (Space/K, arrows, M, F, C, Home, End, 0-9) apply while focus is
 *   in the player, but never take a key the focused control needs for itself:
 *   Space/Enter on a button, anything typed into a select, a text field or
 *   slotted content, the arrows on the volume slider, and any key pressed
 *   with Ctrl, Alt or Meta.
 *
 * Auto-hide
 *   Video controls fade out after three seconds of playback without pointer
 *   or keyboard activity and return on pointer movement, a pointer press, a
 *   key press or focus. They never hide while focus is inside the control
 *   bar, in fullscreen, or for audio.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { t } from "../core/intl.js";
import { escapeHtml, safeUrl } from "../core/html.js";

const HIDE_DELAY_MS = 3000;
const SEEK_STEP_SECONDS = 5;
const VOLUME_STEP = 0.1;
const DEFAULT_RATES = "0.5 0.75 1 1.25 1.5 2";
/* Key of the region name used when the player has no `label`; resolved through t() at use time. */
const DEFAULT_LABEL_KEY = "mj.mediaPlayer.label";

/* Attributes mirrored from light-DOM <source> / <track> children. */
const SOURCE_ATTRIBUTES = ["src", "type", "media"];
const TRACK_ATTRIBUTES = ["kind", "src", "srclang", "label", "default"];

/* data: URLs a media element or text track may load in addition to safeUrl's list. */
const MEDIA_DATA_URL_PATTERN = /^data:(audio|video|text\/vtt)[\/;,]/i;

/* Icon path data (24x24 viewBox). */
const ICON_PLAY = "M8 5v14l11-7z";
const ICON_PAUSE = "M6 19h4V5H6v14zm8-14v14h4V5h-4z";
const ICON_REPLAY = "M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z";
const ICON_VOLUME = "M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z";
const ICON_MUTED = "M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z";
const ICON_FULLSCREEN = "M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z";
const ICON_FULLSCREEN_EXIT = "M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z";

/*
 * The picture, the control bar and the loading / error overlays sit on a
 * dark surround in both themes, so their colours are component custom
 * properties (fallback = default), not page tokens: --mj-player-bg,
 * -controls-bg, -controls-color, -track-bg (slider tracks), -loading-bg,
 * -error-bg and -overlay-color (spinner and error text). The transcript
 * panel is page content and uses the theme tokens.
 */
const STYLES = `
:host { display: block; }

.player {
  position: relative;
  background: var(--mj-player-bg, #000);
  border-radius: var(--mj-player-radius, var(--mj-radius-md));
  overflow: hidden;
}

.media-container {
  position: relative;
  inline-size: 100%;
}
.player.video .media-container {
  aspect-ratio: var(--_ar, 16/9);
}

video { inline-size: 100%; block-size: 100%; display: block; }
audio { display: none; }

.poster {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.poster ::slotted(*) { inline-size: 100%; block-size: 100%; object-fit: cover; }
.player.started .poster,
.player.audio .poster { display: none; }

.controls {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  padding: var(--mj-space-2) var(--mj-space-3);
  background: var(--mj-player-controls-bg, rgba(0, 0, 0, 0.75));
  color: var(--mj-player-controls-color, #fff);
  font-size: var(--mj-font-size-sm);
  transition: opacity var(--mj-motion-fast) var(--mj-motion-ease);
}
/*
 * A video's control bar overlays the bottom of the picture. The picture and
 * the bar share one grid cell, so the bar stays on the picture when the
 * transcript is shown below it instead of covering the transcript.
 */
.player.video {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
}
.player.video .media-container { grid-area: 1 / 1; }
.player.video .controls {
  grid-area: 1 / 1;
  align-self: end;
  position: relative;
  z-index: 1;
}
.player.video .controls.hidden { opacity: 0; pointer-events: none; }

:host([controls="none"]) .controls { display: none; }
:host([controls="minimal"]) .controls > :not(.play-btn):not(.seek) { display: none; }

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
  min-inline-size: 1.5rem;
  min-block-size: 1.5rem;
  flex-shrink: 0;
  font: inherit;
}
.ctrl-btn[hidden] { display: none; }
.ctrl-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.ctrl-btn svg { inline-size: 1em; block-size: 1em; pointer-events: none; }
.captions-btn[aria-pressed="true"] { text-decoration: underline; text-underline-offset: 0.2em; }

.seek {
  flex: 1;
  min-inline-size: 2rem;
  -webkit-appearance: none;
  appearance: none;
  block-size: var(--mj-player-seek-height, 4px);
  border-radius: var(--mj-radius-pill);
  background: var(--mj-player-track-bg, rgba(255, 255, 255, 0.3));
  accent-color: var(--mj-player-seek-color, var(--mj-accent));
  cursor: pointer;
}
.seek[hidden] { display: none; }
.seek:focus-visible,
.volume-range:focus-visible,
.speed-select:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.volume-range {
  inline-size: 4rem;
  -webkit-appearance: none;
  appearance: none;
  block-size: 3px;
  border-radius: var(--mj-radius-pill);
  background: var(--mj-player-track-bg, rgba(255, 255, 255, 0.3));
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
.speed-select option { color: var(--mj-text); background: var(--mj-surface); }

.transcript {
  max-block-size: var(--mj-player-transcript-height, 12rem);
  overflow-y: auto;
  position: relative;
  background: var(--mj-player-transcript-bg, var(--mj-surface));
  padding: var(--mj-space-3);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  border-block-start: 1px solid var(--mj-border);
}
.transcript[hidden] { display: none; }
.cue-list { list-style: none; margin: 0; padding: 0; }
.cue-list[hidden] { display: none; }
.cue {
  display: block;
  inline-size: 100%;
  padding: var(--mj-space-1) 0;
  border: none;
  background: none;
  color: inherit;
  font: inherit;
  text-align: start;
  cursor: pointer;
}
.cue:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.cue[aria-current="true"] { color: var(--mj-player-active-cue-color, var(--mj-accent)); font-weight: var(--mj-font-weight-medium); }
.transcript-empty { margin: 0; color: var(--mj-text-muted); }
.transcript-empty[hidden] { display: none; }

.spinner {
  position: absolute;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  background: var(--mj-player-loading-bg, rgba(0, 0, 0, 0.4));
  color: var(--mj-player-overlay-color, #fff);
}
.spinner.visible { display: flex; }
.spin-ring {
  inline-size: 2rem; block-size: 2rem;
  border: 3px solid color-mix(in srgb, currentColor 40%, transparent);
  border-block-start-color: currentColor;
  border-radius: 50%;
  animation: mj-spin var(--mj-motion-slow) linear infinite;
}
@keyframes mj-spin { to { transform: rotate(360deg); } }

.error-msg {
  display: none;
  margin: 0;
  padding: var(--mj-space-4);
  color: var(--mj-player-overlay-color, #fff);
  text-align: center;
}
.error-msg.visible { display: block; }
.player.video .error-msg.visible {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--mj-player-error-bg, rgba(0, 0, 0, 0.6));
}

.player:fullscreen {
  inline-size: 100%;
  block-size: 100%;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.player:fullscreen .media-container {
  aspect-ratio: auto;
  flex: 1;
  min-block-size: 0;
}
.player:fullscreen video { object-fit: contain; }
.player.video:fullscreen .controls {
  position: absolute;
  inset-block-end: 0;
  inset-inline: 0;
}
`;

function iconMarkup(pathData) {
  const markup = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="${pathData}"/></svg>`
  return markup
}

/*
 * A URL the media element or a text track may load: anything `safeUrl`
 * accepts plus inert audio / video / WebVTT data: URLs. Returns "" otherwise.
 */
function mediaUrl(value) {
  let url = ""
  if (value !== null && value !== undefined) {
    const text = String(value)
    if (MEDIA_DATA_URL_PATTERN.test(text.trim()) === true) {
      url = text
    } else {
      url = safeUrl(text, "")
    }
  }
  return url
}

export class MjMediaPlayer extends MjElement {
  static tagName = "mj-media-player";
  static styles = STYLES;
  static watched = ["type", "src", "poster", "autoplay", "loop", "muted",
    "controls", "show-transcript", "aspect-ratio", "label", "crossorigin", "preload",
    "playback-rates"];

  constructor() {
    super()
    this._media = null
    this._mediaAbort = null
    this._sectionEl = null
    this._mediaContainerEl = null
    this._mediaSlot = null
    this._controlsEl = null
    this._seekEl = null
    this._playBtn = null
    this._timeEl = null
    this._volumeRange = null
    this._muteBtn = null
    this._speedSelect = null
    this._captionsBtn = null
    this._fsBtn = null
    this._transcriptEl = null
    this._transcriptSlot = null
    this._cueListEl = null
    this._transcriptEmptyEl = null
    this._spinnerEl = null
    this._errorEl = null
    this._hideTimer = null
    this._childObserver = null

    /* Signatures of the mirrored <source> / <track> children. */
    this._sourceSignature = null
    this._trackSignature = null

    /* The text track the transcript is built from, and its cue buttons. */
    this._transcriptTrack = null
    this._cueButtons = []

    /* Whether the transcript panel was open at the last sync; null before the first. */
    this._transcriptOpen = null

    /* True after `ended`, until playback starts again. */
    this._ended = false
  }

  render() {
    const markup = `
      <section part="player" class="player video" aria-label="">
        <div class="media-container" part="media-container">
          <div class="media-slot"></div>
          <div class="poster" part="poster"><slot name="poster"></slot></div>
          <div class="spinner" part="loading" aria-hidden="true">
            <div class="spin-ring"></div>
          </div>
          <p class="error-msg" part="error" role="alert"></p>
        </div>
        <div class="controls" part="controls" role="group" aria-label="${escapeHtml(t("mj.mediaPlayer.mediaControls"))}">
          <button type="button" class="ctrl-btn play-btn" part="play-btn" aria-label="${escapeHtml(t("mj.mediaPlayer.play"))}">${iconMarkup(ICON_PLAY)}</button>
          <input type="range" class="seek" part="seek"
            aria-label="${escapeHtml(t("mj.mediaPlayer.seek"))}" min="0" max="0" value="0" step="0.1" />
          <span class="time" part="time">0:00 / 0:00</span>
          <button type="button" class="ctrl-btn mute-btn" part="volume" aria-label="${escapeHtml(t("mj.mediaPlayer.mute"))}">${iconMarkup(ICON_VOLUME)}</button>
          <input type="range" class="volume-range" aria-label="${escapeHtml(t("mj.mediaPlayer.volume"))}" min="0" max="1" step="0.05" value="1" />
          <select class="speed-select" part="speed" aria-label="${escapeHtml(t("mj.mediaPlayer.playbackSpeed"))}"></select>
          <button type="button" class="ctrl-btn captions-btn" part="captions-btn" aria-label="${escapeHtml(t("mj.mediaPlayer.captions"))}" aria-pressed="false" hidden>${escapeHtml(t("mj.mediaPlayer.captionsShort"))}</button>
          <button type="button" class="ctrl-btn fs-btn" part="fullscreen-btn" aria-label="${escapeHtml(t("mj.mediaPlayer.fullscreen"))}" hidden>${iconMarkup(ICON_FULLSCREEN)}</button>
          <slot name="controls-end"></slot>
        </div>
        <div class="transcript" part="transcript" role="log" aria-live="off" aria-label="${escapeHtml(t("mj.mediaPlayer.transcript"))}" hidden>
          <slot name="transcript"></slot>
          <ol class="cue-list"></ol>
          <p class="transcript-empty" hidden>${escapeHtml(t("mj.mediaPlayer.noTranscript"))}</p>
        </div>
      </section>
    `
    return markup
  }

  afterRender() {
    this._sectionEl = this.$("section")
    this._mediaContainerEl = this.$(".media-container")
    this._mediaSlot = this.$(".media-slot")
    this._spinnerEl = this.$(".spinner")
    this._errorEl = this.$(".error-msg")
    this._controlsEl = this.$(".controls")
    this._playBtn = this.$(".play-btn")
    this._seekEl = this.$(".seek")
    this._timeEl = this.$(".time")
    this._muteBtn = this.$(".mute-btn")
    this._volumeRange = this.$(".volume-range")
    this._speedSelect = this.$(".speed-select")
    this._captionsBtn = this.$(".captions-btn")
    this._fsBtn = this.$(".fs-btn")
    this._transcriptEl = this.$(".transcript")
    this._transcriptSlot = this.$("slot[name='transcript']")
    this._cueListEl = this.$(".cue-list")
    this._transcriptEmptyEl = this.$(".transcript-empty")

    this._media = null
    this._transcriptOpen = null

    this._buildMedia()
    this._buildSpeedOptions()
    this._wireControls()
    this._watchChildren()
    this._applyAttrs()
    return
  }

  /* ----- media element ----- */

  _type() {
    const type = this.getAttribute("type") === "audio" ? "audio" : "video"
    return type
  }

  /*
   * Create the native media element for the current `type`, replacing any
   * previous one, and bring it in line with the attributes and the
   * light-DOM <source> / <track> children.
   */
  _buildMedia() {
    if (this._mediaAbort !== null) {
      this._mediaAbort.abort()
      this._mediaAbort = null
    }
    if (this._media !== null) {
      this._media.pause()
      this._media.remove()
      this._media = null
    }

    const type = this._type()
    const el = document.createElement(type)
    el.setAttribute("part", "media")
    if (type === "video") {
      el.setAttribute("playsinline", "")
    }

    this._sectionEl.classList.toggle("video", type === "video")
    this._sectionEl.classList.toggle("audio", type === "audio")
    this._sectionEl.classList.remove("started")

    this._media = el
    this._ended = false
    this._sourceSignature = null
    this._trackSignature = null
    this._transcriptTrack = null

    this._applyMediaAttrs()

    const abort = new AbortController()
    this._mediaAbort = abort
    const options = { signal: abort.signal }
    this.listen(el, "play", () => this._onPlay(), options)
    this.listen(el, "pause", () => this._onPause(), options)
    this.listen(el, "ended", () => this._onEnded(), options)
    this.listen(el, "timeupdate", () => this._onTimeUpdate(), options)
    this.listen(el, "durationchange", () => this._onDurationChange(), options)
    this.listen(el, "volumechange", () => this._onVolumeChange(), options)
    this.listen(el, "ratechange", () => this._onRateChange(), options)
    this.listen(el, "waiting", () => this._onWaiting(), options)
    this.listen(el, "playing", () => this._onPlaying(), options)
    this.listen(el, "loadeddata", () => this._clearError(), options)
    this.listen(el, "error", () => this._onMediaError(), options)
    this.listen(el.textTracks, "addtrack", () => this._onTracksChanged(), options)
    this.listen(el.textTracks, "removetrack", () => this._onTracksChanged(), options)
    this.listen(el.textTracks, "change", () => this._onTracksChanged(), options)

    this._mediaSlot.appendChild(el)
    this._syncSources()

    this._resetControls()
    this._syncFullscreenButton()
    return
  }

  /* Mirror the media-related host attributes onto the native element. */
  _applyMediaAttrs() {
    const el = this._media
    if (el === null) {
      return
    }

    const src = mediaUrl(this.getAttribute("src"))
    if (src.length > 0) {
      if (el.getAttribute("src") !== src) {
        el.setAttribute("src", src)
      }
    } else if (el.hasAttribute("src") === true) {
      /* Removing the source stops whatever was playing. */
      el.pause()
      el.removeAttribute("src")
      el.load()
    }

    el.setAttribute("preload", this.getAttribute("preload") || "metadata")

    const crossorigin = this.getAttribute("crossorigin")
    if (crossorigin !== null) {
      el.setAttribute("crossorigin", crossorigin)
    } else {
      el.removeAttribute("crossorigin")
    }

    if (el.localName === "video") {
      const poster = safeUrl(this.getAttribute("poster") || "", "")
      if (poster.length > 0) {
        el.setAttribute("poster", poster)
      } else {
        el.removeAttribute("poster")
      }
    }

    el.loop = this.hasAttribute("loop")
    el.muted = this.hasAttribute("muted")

    /* `volumechange` arrives later; the mute button reflects the attribute at once. */
    if (this._muteBtn !== null) {
      this._onVolumeChange(true)
    }

    let autoplay = this.hasAttribute("autoplay")
    if (autoplay === true) {
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
      if (reduced === true) {
        console.warn("<mj-media-player>: autoplay suppressed due to prefers-reduced-motion.")
        autoplay = false
      }
    }
    el.autoplay = autoplay
    return
  }

  /* ----- light-DOM <source> / <track> children ----- */

  _watchChildren() {
    const observer = new MutationObserver(() => { this._syncSources() })
    observer.observe(this, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: SOURCE_ATTRIBUTES.concat(TRACK_ATTRIBUTES)
    })
    this._childObserver = observer
    this.onTeardown(() => {
      observer.disconnect()
      if (this._childObserver === observer) {
        this._childObserver = null
      }
    })
    return
  }

  /* One mirrored child as { tag, attributes: [[name, value], ...] }. */
  _describeChild(child) {
    const tag = child.localName
    const names = tag === "source" ? SOURCE_ATTRIBUTES : TRACK_ATTRIBUTES
    const attributes = []

    for (let index = 0; index < names.length; index = index + 1) {
      const name = names[index]
      if (child.hasAttribute(name) === true) {
        let value = child.getAttribute(name)
        if (name === "src") {
          value = mediaUrl(value)
        }
        attributes.push([name, value])
      }
    }

    const description = { tag: tag, attributes: attributes }
    return description
  }

  /*
   * Copy the light-DOM <source> and <track> children into the native media
   * element. Sources and tracks are rebuilt independently, and only when
   * they changed, so a caption edit does not restart the media and a source
   * edit does not reset the caption state.
   */
  _syncSources() {
    if (this._media === null) {
      return
    }

    const sources = []
    const tracks = []
    const children = Array.from(this.children)
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      /* A child without a loadable `src` (absent, or a rejected scheme) is not mirrored. */
      if (child.localName === "source" || child.localName === "track") {
        const usable = mediaUrl(child.getAttribute("src")).length > 0
        if (usable === true && child.localName === "source") {
          sources.push(this._describeChild(child))
        } else if (usable === true) {
          tracks.push(this._describeChild(child))
        }
      }
    }

    const sourceSignature = JSON.stringify(sources)
    if (sourceSignature !== this._sourceSignature) {
      const firstSync = this._sourceSignature === null
      this._sourceSignature = sourceSignature
      this._replaceMirrored("source", sources)
      if (firstSync === false && this._media.hasAttribute("src") === false) {
        this._clearError()
        this._media.load()
      }
    }

    const trackSignature = JSON.stringify(tracks)
    if (trackSignature !== this._trackSignature) {
      this._trackSignature = trackSignature
      this._replaceMirrored("track", tracks)
      this._onTracksChanged()
    }
    return
  }

  _replaceMirrored(tag, descriptions) {
    const existing = this._media.querySelectorAll(tag)
    for (let index = 0; index < existing.length; index = index + 1) {
      existing[index].remove()
    }

    for (let index = 0; index < descriptions.length; index = index + 1) {
      const description = descriptions[index]
      const el = document.createElement(tag)
      for (let attr = 0; attr < description.attributes.length; attr = attr + 1) {
        const pair = description.attributes[attr]
        el.setAttribute(pair[0], pair[1])
      }
      if (tag === "track") {
        /* Cues arrive asynchronously; the transcript is rebuilt when they do. */
        this.listen(el, "load", () => this._buildTranscript(), { signal: this._mediaAbort.signal })
      }
      this._media.appendChild(el)
    }
    return
  }

  /* ----- controls ----- */

  _buildSpeedOptions() {
    const ratesText = this.getAttribute("playback-rates") || DEFAULT_RATES
    let rates = ratesText.split(/\s+/).map(Number).filter((rate) => Number.isFinite(rate) === true && rate > 0)
    if (rates.length === 0) {
      rates = DEFAULT_RATES.split(" ").map(Number)
    }

    const current = this._media !== null ? this._media.playbackRate : 1
    this._speedSelect.textContent = ""
    for (let index = 0; index < rates.length; index = index + 1) {
      const option = document.createElement("option")
      option.value = String(rates[index])
      option.textContent = t("mj.mediaPlayer.speedOption", { rate: rates[index] })
      option.selected = rates[index] === current
      this._speedSelect.appendChild(option)
    }
    return
  }

  _wireControls() {
    this.listen(this._playBtn, "click", () => this._togglePlay())
    this.listen(this._seekEl, "input", () => this._onSeekInput())
    this.listen(this._muteBtn, "click", () => this._toggleMute())
    this.listen(this._volumeRange, "input", () => {
      if (this._media !== null) {
        this._media.volume = parseFloat(this._volumeRange.value)
        if (this._media.volume > 0) {
          this._media.muted = false
        }
      }
    })
    this.listen(this._speedSelect, "change", () => {
      const rate = parseFloat(this._speedSelect.value)
      if (this._media !== null && Number.isFinite(rate) === true) {
        this._media.playbackRate = rate
        this.emit("mj-rate-change", { playbackRate: rate })
      }
    })
    this.listen(this._captionsBtn, "click", () => this._toggleCaptions())
    this.listen(this._fsBtn, "click", () => this._toggleFullscreen())
    this.listen(this._transcriptSlot, "slotchange", () => this._buildTranscript())
    this.listen(this._cueListEl, "click", (event) => this._onCueClick(event))

    this.listen(this._sectionEl, "keydown", (event) => this._onKeyDown(event))

    /* Any sign of activity brings the control bar back and restarts the timer. */
    const wake = () => {
      this._showControls()
      this._scheduleHide()
    }
    this.listen(this._sectionEl, "pointermove", wake)
    this.listen(this._sectionEl, "pointerdown", wake)
    this.listen(this._sectionEl, "focusin", wake)
    this.listen(this._sectionEl, "focusout", () => this._scheduleHide())
    this.listen(this._sectionEl, "pointerleave", () => this._scheduleHide())

    this.listen(document, "fullscreenchange", () => this._syncFullscreenButton())

    this.onTeardown(() => { this._clearHideTimer() })
    return
  }

  /* Put the control bar back into its idle state for a new media element. */
  _resetControls() {
    this._setPlayButton(t("mj.mediaPlayer.play"), ICON_PLAY)
    this._seekEl.value = "0"
    this._seekEl.setAttribute("max", "0")
    this._seekEl.hidden = false
    this._timeEl.textContent = "0:00 / 0:00"
    this._spinnerEl.classList.remove("visible")
    this._clearError()
    this._showControls()
    this._onVolumeChange(true)
    this._onTracksChanged()
    return
  }

  _applyAttrs() {
    const label = this.getAttribute("label") || t(DEFAULT_LABEL_KEY)
    this._sectionEl.setAttribute("aria-label", label)

    const ratio = this.getAttribute("aspect-ratio") || "16/9"
    this._mediaContainerEl.style.setProperty("--_ar", ratio)

    this._syncTranscriptVisibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._media === null || this._media === undefined) {
      return
    }

    if (name === "type") {
      if (this._media.localName !== this._type()) {
        this._buildMedia()
        this._buildTranscript()
      }
    } else if (name === "src") {
      this._clearError()
      this._applyMediaAttrs()
    } else if (name === "poster" || name === "loop" || name === "muted" ||
        name === "preload" || name === "crossorigin" || name === "autoplay") {
      this._applyMediaAttrs()
    } else if (name === "playback-rates") {
      this._buildSpeedOptions()
    } else if (name === "controls") {
      this._showControls()
    } else if (name === "label" || name === "aspect-ratio" || name === "show-transcript") {
      this._applyAttrs()
    }
    return
  }

  _setPlayButton(label, iconPath) {
    if (this._playBtn.getAttribute("aria-label") !== label) {
      this._playBtn.setAttribute("aria-label", label)
      this._playBtn.innerHTML = iconMarkup(iconPath)
    }
    return
  }

  _togglePlay() {
    if (this._media === null) { return }
    if (this._media.paused === true || this._media.ended === true) {
      const started = this._media.play()
      if (started !== undefined && typeof started.catch === "function") {
        /* A blocked or unsupported play is reported by the `error` event or left paused. */
        started.catch((error) => {
          if (error !== null && error !== undefined && error.name === "NotAllowedError") {
            console.warn("<mj-media-player>: playback was blocked by the browser.", error)
          }
        })
      }
    } else {
      this._media.pause()
    }
    return
  }

  _onPlay() {
    this._ended = false
    this._sectionEl.classList.add("started")
    this._setPlayButton(t("mj.mediaPlayer.pause"), ICON_PAUSE)
    this.emit("mj-play", { currentTime: this._media.currentTime })
    this._scheduleHide()
    return
  }

  _onPause() {
    if (this._ended === false) {
      this._setPlayButton(t("mj.mediaPlayer.play"), ICON_PLAY)
    }
    this.emit("mj-pause", { currentTime: this._media.currentTime })
    this._showControls()
    return
  }

  _onEnded() {
    this._ended = true
    this._setPlayButton(t("mj.mediaPlayer.replay"), ICON_REPLAY)
    this.emit("mj-ended", {})
    this._showControls()
    return
  }

  _isLive() {
    const live = this._media !== null && this._media.duration === Infinity
    return live
  }

  _duration() {
    const raw = this._media !== null ? this._media.duration : 0
    const duration = Number.isFinite(raw) === true ? raw : 0
    return duration
  }

  _onTimeUpdate() {
    if (this._media === null) { return }
    const currentTime = this._media.currentTime
    const duration = this._duration()

    if (this._isLive() === true) {
      this._timeEl.textContent = t("mj.mediaPlayer.live")
    } else {
      this._seekEl.value = String(currentTime)
      this._timeEl.textContent = `${this._fmt(currentTime)} / ${this._fmt(duration)}`
      this._seekEl.setAttribute(
        "aria-valuetext",
        t("mj.mediaPlayer.seekValue", { current: this._fmt(currentTime), duration: this._fmt(duration) })
      )
    }

    this._highlightActiveCues()
    return
  }

  _onDurationChange() {
    if (this._media === null) { return }
    const duration = this._duration()
    this._seekEl.setAttribute("max", String(duration))
    this._seekEl.hidden = this._isLive() === true
    this._onTimeUpdate()
    return
  }

  _onVolumeChange(silent) {
    if (this._media === null) { return }
    const muted = this._media.muted === true || this._media.volume === 0
    this._volumeRange.value = String(muted === true ? 0 : this._media.volume)
    this._volumeRange.setAttribute("aria-valuetext", `${Math.round((muted === true ? 0 : this._media.volume) * 100)}%`)

    const label = muted === true ? t("mj.mediaPlayer.unmute") : t("mj.mediaPlayer.mute")
    if (this._muteBtn.getAttribute("aria-label") !== label || this._muteBtn.firstElementChild === null) {
      this._muteBtn.setAttribute("aria-label", label)
      this._muteBtn.innerHTML = iconMarkup(muted === true ? ICON_MUTED : ICON_VOLUME)
    }

    if (silent !== true) {
      this.emit("mj-volume-change", { volume: this._media.volume, muted: this._media.muted })
    }
    return
  }

  _onRateChange() {
    if (this._media === null) { return }
    const rate = String(this._media.playbackRate)
    const options = this._speedSelect.options
    for (let index = 0; index < options.length; index = index + 1) {
      options[index].selected = options[index].value === rate
    }
    return
  }

  _onWaiting() {
    this._spinnerEl.classList.add("visible")
    announce(t("mj.mediaPlayer.buffering"), "polite")
    return
  }

  _onPlaying() {
    this._spinnerEl.classList.remove("visible")
    this._clearError()
    return
  }

  _onMediaError() {
    const code = this._media !== null && this._media.error !== null ? this._media.error.code : 0
    const message = t("mj.mediaPlayer.mediaError", { code: code })
    this._spinnerEl.classList.remove("visible")
    this._errorEl.textContent = message
    this._errorEl.classList.add("visible")
    this.emit("mj-error", { code: code, message: message })
    return
  }

  _clearError() {
    this._errorEl.textContent = ""
    this._errorEl.classList.remove("visible")
    return
  }

  _onSeekInput() {
    if (this._media === null) { return }
    this._seekTo(parseFloat(this._seekEl.value))
    return
  }

  /* Move the playhead, clamped to the media, and report the seek. */
  _seekTo(seconds) {
    if (this._media === null || Number.isFinite(seconds) === false) { return }
    const previous = this._media.currentTime
    const target = Math.max(0, Math.min(this._duration(), seconds))
    this._media.currentTime = target
    this.emit("mj-seek", { currentTime: target, previousTime: previous })
    return
  }

  _changeVolume(delta) {
    if (this._media === null) { return }
    const next = Math.max(0, Math.min(1, this._media.volume + delta))
    this._media.volume = Math.round(next * 100) / 100
    if (next > 0) {
      this._media.muted = false
    }
    return
  }

  _toggleMute() {
    if (this._media === null) { return }
    this._media.muted = this._media.muted === false
    return
  }

  /* ----- captions ----- */

  _captionTracks() {
    const found = []
    if (this._media !== null) {
      const tracks = this._media.textTracks
      for (let index = 0; index < tracks.length; index = index + 1) {
        const kind = tracks[index].kind
        if (kind === "captions" || kind === "subtitles") {
          found.push(tracks[index])
        }
      }
    }
    return found
  }

  /* Text tracks were added, removed or switched: refresh button and transcript. */
  _onTracksChanged() {
    if (this._media === null || this._captionsBtn === null) { return }
    const tracks = this._captionTracks()
    this._captionsBtn.hidden = tracks.length === 0

    let showing = false
    for (let index = 0; index < tracks.length; index = index + 1) {
      if (tracks[index].mode === "showing") {
        showing = true
      }
    }
    this._captionsBtn.setAttribute("aria-pressed", showing === true ? "true" : "false")

    this._buildTranscript()
    return
  }

  /* Off -> first track -> next track ... -> off. A single track simply toggles. */
  _toggleCaptions() {
    const tracks = this._captionTracks()
    if (tracks.length === 0) { return }

    let showingIndex = -1
    for (let index = 0; index < tracks.length; index = index + 1) {
      if (tracks[index].mode === "showing") {
        showingIndex = index
      }
    }

    const nextIndex = showingIndex + 1
    for (let index = 0; index < tracks.length; index = index + 1) {
      const wanted = index === nextIndex ? "showing" : "hidden"
      if (tracks[index].mode !== wanted) {
        tracks[index].mode = wanted
      }
    }

    const active = nextIndex < tracks.length ? tracks[nextIndex] : null
    this._captionsBtn.setAttribute("aria-pressed", active !== null ? "true" : "false")
    this.emit("mj-captions-change", { track: active !== null ? (active.label || active.language || "") : null })
    this._buildTranscript()
    return
  }

  /* ----- transcript ----- */

  _syncTranscriptVisibility() {
    const open = this.hasAttribute("show-transcript")
    this._transcriptEl.hidden = open === false

    if (this._transcriptOpen !== null && this._transcriptOpen !== open) {
      this.emit("mj-transcript-toggle", { open: open })
    }
    this._transcriptOpen = open

    this._buildTranscript()
    return
  }

  /*
   * Fill the transcript panel from the cues of the active caption track
   * (the one showing, else the first). Slotted transcript content replaces
   * the generated list.
   */
  _buildTranscript() {
    if (this._transcriptEl === null || this._media === null) { return }

    const slotted = this._transcriptSlot.assignedNodes({ flatten: true })
    const hasSlotted = slotted.length > 0
    const open = this.hasAttribute("show-transcript")

    this._cueListEl.textContent = ""
    this._cueButtons = []
    this._transcriptTrack = null
    this._cueListEl.hidden = hasSlotted === true
    this._transcriptEmptyEl.hidden = true

    if (open === false || hasSlotted === true) {
      return
    }

    const tracks = this._captionTracks()
    let track = null
    for (let index = 0; index < tracks.length; index = index + 1) {
      if (track === null || (tracks[index].mode === "showing" && track.mode !== "showing")) {
        track = tracks[index]
      }
    }

    if (track !== null && track.mode === "disabled") {
      /* A disabled track never loads its cues; "hidden" loads without displaying. */
      track.mode = "hidden"
    }

    const cues = track !== null && track.cues !== null ? track.cues : []
    for (let index = 0; index < cues.length; index = index + 1) {
      const cue = cues[index]
      const item = document.createElement("li")
      const button = document.createElement("button")
      button.type = "button"
      button.className = "cue"
      button.setAttribute("data-start", String(cue.startTime))
      /* Cue text may carry WebVTT markup such as <v Name>; show the words only. */
      button.textContent = String(cue.text || "").replace(/<[^>]*>/g, "")
      item.appendChild(button)
      this._cueListEl.appendChild(item)
      this._cueButtons.push({ button: button, start: cue.startTime, end: cue.endTime })
    }

    this._transcriptTrack = track
    this._transcriptEmptyEl.hidden = this._cueButtons.length > 0
    this._highlightActiveCues()
    return
  }

  _highlightActiveCues() {
    if (this._media === null || this._cueButtons.length === 0) { return }
    const now = this._media.currentTime

    for (let index = 0; index < this._cueButtons.length; index = index + 1) {
      const entry = this._cueButtons[index]
      const active = now >= entry.start && now < entry.end
      const wasActive = entry.button.getAttribute("aria-current") === "true"
      if (active === true && wasActive === false) {
        entry.button.setAttribute("aria-current", "true")
        /* Scroll inside the panel only; scrollIntoView would move the page too. */
        const panel = this._transcriptEl
        const top = entry.button.offsetTop
        const bottom = top + entry.button.offsetHeight
        if (top < panel.scrollTop || bottom > panel.scrollTop + panel.clientHeight) {
          panel.scrollTop = Math.max(0, top - panel.clientHeight / 2)
        }
      } else if (active === false && wasActive === true) {
        entry.button.removeAttribute("aria-current")
      }
    }
    return
  }

  _onCueClick(event) {
    const button = event.target instanceof Element ? event.target.closest(".cue") : null
    if (button !== null) {
      this._seekTo(parseFloat(button.getAttribute("data-start")))
    }
    return
  }

  /* ----- fullscreen ----- */

  _isFullscreen() {
    const active = this.shadowRoot.fullscreenElement === this._sectionEl
    return active
  }

  _fullscreenSupported() {
    const supported = this._type() === "video" &&
      typeof this._sectionEl.requestFullscreen === "function" &&
      document.fullscreenEnabled !== false
    return supported
  }

  _syncFullscreenButton() {
    if (this._fsBtn === null) { return }
    const supported = this._fullscreenSupported()
    this._fsBtn.hidden = supported === false

    const active = this._isFullscreen()
    const label = active === true ? t("mj.mediaPlayer.exitFullscreen") : t("mj.mediaPlayer.fullscreen")
    if (this._fsBtn.getAttribute("aria-label") !== label) {
      this._fsBtn.setAttribute("aria-label", label)
      this._fsBtn.innerHTML = iconMarkup(active === true ? ICON_FULLSCREEN_EXIT : ICON_FULLSCREEN)
    }

    if (active === true) {
      this._showControls()
    } else {
      this._scheduleHide()
    }
    return
  }

  /* The whole player goes fullscreen so the control bar comes along. */
  _toggleFullscreen() {
    if (this._fullscreenSupported() === false) { return }

    if (this._isFullscreen() === true) {
      document.exitFullscreen()
      return
    }

    let request = null
    try {
      request = this._sectionEl.requestFullscreen()
    } catch (error) {
      request = Promise.reject(error)
    }
    if (request !== undefined && request !== null && typeof request.catch === "function") {
      request.catch((error) => {
        console.warn("<mj-media-player>: fullscreen request rejected.", error)
        this._fsBtn.hidden = true
      })
    }
    return
  }

  /* ----- keyboard ----- */

  /*
   * True when the focused element needs `key` for itself, so the player
   * shortcut must not run.
   */
  _keyBelongsToTarget(target, key) {
    if (!(target instanceof Element)) {
      return false
    }

    /* Slotted content (controls-end, transcript, poster) keeps all of its keys. */
    if (target.getRootNode() !== this.shadowRoot) {
      return true
    }

    const tag = target.localName
    let belongs = false

    if (tag === "select" || tag === "textarea" || target.isContentEditable === true) {
      belongs = true
    } else if (tag === "button" || tag === "a") {
      belongs = key === " " || key === "Enter"
    } else if (tag === "input") {
      if (target === this._seekEl) {
        /* The seek slider's arrows, Home and End are handled as seek shortcuts. */
        belongs = key === "PageUp" || key === "PageDown"
      } else if (target.type === "range") {
        belongs = key.startsWith("Arrow") || key === "Home" || key === "End" ||
          key === "PageUp" || key === "PageDown"
      } else {
        belongs = true
      }
    }

    return belongs
  }

  _onKeyDown(event) {
    if (this._media === null) { return }

    /* A key press is activity, whatever it does. */
    this._showControls()
    this._scheduleHide()

    if (event.ctrlKey === true || event.metaKey === true || event.altKey === true) {
      return
    }
    if (event.defaultPrevented === true) {
      return
    }

    const key = event.key
    const path = typeof event.composedPath === "function" ? event.composedPath() : []
    const target = path.length > 0 ? path[0] : event.target
    if (this._keyBelongsToTarget(target, key) === true) {
      return
    }

    const onSeekSlider = target === this._seekEl
    const media = this._media
    let handled = true

    if (key === " " || key === "k" || key === "K") {
      this._togglePlay()
    } else if (key === "ArrowLeft" || (onSeekSlider === true && key === "ArrowDown")) {
      this._seekTo(media.currentTime - SEEK_STEP_SECONDS)
    } else if (key === "ArrowRight" || (onSeekSlider === true && key === "ArrowUp")) {
      this._seekTo(media.currentTime + SEEK_STEP_SECONDS)
    } else if (key === "ArrowUp") {
      this._changeVolume(VOLUME_STEP)
    } else if (key === "ArrowDown") {
      this._changeVolume(-VOLUME_STEP)
    } else if (key === "m" || key === "M") {
      this._toggleMute()
    } else if (key === "f" || key === "F") {
      this._toggleFullscreen()
    } else if (key === "c" || key === "C") {
      this._toggleCaptions()
    } else if (key === "Home") {
      this._seekTo(0)
    } else if (key === "End") {
      this._seekTo(this._duration())
    } else if (/^[0-9]$/.test(key) === true) {
      this._seekTo(this._duration() * (parseInt(key, 10) / 10))
    } else {
      handled = false
    }

    if (handled === true) {
      event.preventDefault()
    }
    return
  }

  /* ----- control bar visibility ----- */

  _clearHideTimer() {
    if (this._hideTimer !== null) {
      clearTimeout(this._hideTimer)
      this._hideTimer = null
    }
    return
  }

  _showControls() {
    this._controlsEl.classList.remove("hidden")
    this._clearHideTimer()
    return
  }

  /* Whether the control bar is allowed to fade out right now. */
  _mayHideControls() {
    const allowed = this._media !== null &&
      this._type() === "video" &&
      this._media.paused === false &&
      this._isFullscreen() === false &&
      this._controlsEl.matches(":focus-within") === false
    return allowed
  }

  _scheduleHide() {
    this._clearHideTimer()
    if (this._mayHideControls() === false) { return }

    this._hideTimer = setTimeout(() => {
      this._hideTimer = null
      if (this._mayHideControls() === true) {
        this._controlsEl.classList.add("hidden")
      }
    }, HIDE_DELAY_MS)
    return
  }

  _fmt(seconds) {
    const total = Math.floor(seconds) || 0
    const hours = Math.floor(total / 3600)
    const minutes = Math.floor((total % 3600) / 60)
    const secs = total % 60
    const paddedSeconds = `${secs < 10 ? "0" : ""}${secs}`
    let formatted = `${minutes}:${paddedSeconds}`
    if (hours > 0) {
      formatted = `${hours}:${minutes < 10 ? "0" : ""}${minutes}:${paddedSeconds}`
    }
    return formatted
  }

  onDisconnected() {
    this._clearHideTimer()
    if (this._mediaAbort !== null) {
      this._mediaAbort.abort()
      this._mediaAbort = null
    }
    if (this._media !== null) {
      this._media.pause()
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

  get muted() { return this._media === null ? this.hasAttribute("muted") : this._media.muted }
  set muted(v) { if (this._media !== null) { this._media.muted = Boolean(v) } }

  get playbackRate() { return this._media === null ? 1 : this._media.playbackRate }
  set playbackRate(v) { if (this._media !== null) { this._media.playbackRate = v } }
}
