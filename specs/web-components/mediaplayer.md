# Media Player Spec

- **Tag:** `<mj-media-player>`
- **Class / file:** `MjMediaPlayer` / `mjmediaplayer.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Video player, Audio player, Media controls
- **Phase:** P2
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-media-player>` wraps a native `<video>` or `<audio>` element and provides a
fully keyboard-operable, accessible control bar with play/pause, seek, volume,
playback speed, captions/subtitles, and transcript support. It does not implement
its own codec or streaming engine; the native media element handles all decoding.
The Media controls part is composable and may be used standalone to replace a
browser's default controls for an existing `<video>` or `<audio>` in the light DOM.

## 2. When to use / when not to use

**Use** for any inline video or audio that requires branded controls, captions,
or a transcript panel.

**Do not use** for background video that is purely decorative (use a plain
`<video autoplay muted>` and hide it from assistive technology); do not use for
embedded third-party iframes (YouTube, Vimeo) — those require their own SDK wrappers.

## 3. Anatomy

- **Media container** (`::part(media-container)`) — holds the native `<video>` or
  `<audio>` element; aspect-ratio reserved for video.
- **Video/Audio element** (`::part(media)`) — the native media element; all
  source elements are slotted as children.
- **Controls bar** (`::part(controls)`) — absolutely positioned bar at the bottom
  of video or below audio; contains all control sub-parts.
- **Play button** (`::part(play-btn)`) — toggles play/pause.
- **Seek bar** (`::part(seek)`) — range slider for position scrubbing.
- **Time display** (`::part(time)`) — current time / duration text.
- **Volume control** (`::part(volume)`) — mute toggle + range slider.
- **Speed control** (`::part(speed)`) — playback rate selector (Select/listbox).
- **Captions button** (`::part(captions-btn)`) — toggles caption track display.
- **Transcript panel** (`::part(transcript)`) — scrollable text panel that
  auto-scrolls to the active cue; hidden unless `show-transcript` is set.
- **Fullscreen button** (`::part(fullscreen-btn)`) — video only; requests
  fullscreen on the container.
- **Poster** (`::part(poster)`) — displayed before playback starts; native `poster`
  attribute used on the `<video>`.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Video | `type="video"` (default) | Renders `<video>` with fullscreen; aspect-ratio reservation |
| Audio | `type="audio"` | Renders `<audio>`; no fullscreen or poster; compact bar layout |
| With transcript | `show-transcript` (boolean) | Transcript panel visible alongside/below media |
| Autoplay | `autoplay` | Sets `autoplay` on the media element; blocked if `prefers-reduced-motion: reduce` |
| No controls | `controls="none"` | Hides control bar; media plays programmatically only |
| Minimal controls | `controls="minimal"` | Shows only play/pause and seek bar |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `type` | `"video"\|"audio"` | `"video"` | Yes | Which native media element to render |
| `src` | `string` | `""` | Yes | Primary media source URL |
| `poster` | `string` | `""` | Yes | Video poster image URL |
| `autoplay` | `boolean` | `false` | Yes | Autoplay on load (suppressed under `prefers-reduced-motion: reduce`) |
| `loop` | `boolean` | `false` | Yes | Loop playback |
| `muted` | `boolean` | `false` | Yes | Mute on load |
| `controls` | `"full"\|"minimal"\|"none"` | `"full"` | Yes | Control bar visibility level |
| `show-transcript` | `boolean` | `false` | Yes | Show the transcript panel |
| `aspect-ratio` | `string` | `"16/9"` | Yes | CSS aspect-ratio for video container |
| `playback-rates` | `string` | `"0.5 0.75 1 1.25 1.5 2"` | Yes | Space-separated list of available playback rates |
| `label` | `string` | `""` | Yes | Accessible label for the player region (e.g. "Interview with Ada Lovelace") |
| `crossorigin` | `"anonymous"\|"use-credentials"` | `""` | Yes | Forwarded to the media element |
| `preload` | `"none"\|"metadata"\|"auto"` | `"metadata"` | Yes | Forwarded to the media element |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `currentTime` | `number` | Read/write; current playback position in seconds |
| `duration` | `number` | Read-only; media duration in seconds |
| `paused` | `boolean` | Read-only; `true` when playback is paused |
| `muted` | `boolean` | Read/write; mute state (also reflected as attribute) |
| `volume` | `number` | Read/write; volume level 0–1 |
| `playbackRate` | `number` | Read/write; current playback rate |
| `textTracks` | `TextTrackList` | Read-only; forwarded from the native media element |
| `mediaElement` | `HTMLMediaElement` | Read-only; reference to the internal `<video>` or `<audio>` |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | `<source>` and `<track>` elements forwarded to the media element |
| `transcript` | Custom transcript content replacing the auto-generated transcript panel |
| `poster` | Custom poster content (e.g. `<mj-image>`) replacing the `poster` attribute |
| `controls-end` | Additional control buttons appended to the right end of the control bar |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-play` | `{ currentTime: number }` | Yes | No | Fired when playback starts |
| `mj-pause` | `{ currentTime: number }` | Yes | No | Fired when playback pauses |
| `mj-ended` | `{}` | Yes | No | Fired when media reaches the end |
| `mj-seek` | `{ currentTime: number, previousTime: number }` | Yes | No | Fired after a seek completes |
| `mj-volume-change` | `{ volume: number, muted: boolean }` | Yes | No | Fired on volume or mute change |
| `mj-rate-change` | `{ playbackRate: number }` | Yes | No | Fired on playback rate change |
| `mj-captions-change` | `{ track: string \| null }` | Yes | No | Fired when caption track is toggled on/off; `track` is the track label |
| `mj-transcript-toggle` | `{ open: boolean }` | Yes | No | Fired when the transcript panel is shown/hidden |
| `mj-error` | `{ code: number, message: string }` | Yes | No | Fired on media element error |

## 9. CSS parts & custom properties

**Parts**
- `::part(media-container)`, `::part(media)`, `::part(controls)`
- `::part(play-btn)`, `::part(seek)`, `::part(time)`
- `::part(volume)`, `::part(speed)`, `::part(captions-btn)`
- `::part(fullscreen-btn)`, `::part(transcript)`, `::part(poster)`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-player-controls-bg` | `rgba(0,0,0,0.7)` | Control bar background |
| `--mj-player-controls-color` | `var(--mj-color-text-on-dark)` | Icon/text color in control bar |
| `--mj-player-seek-color` | `var(--mj-color-primary)` | Filled portion of seek bar |
| `--mj-player-seek-height` | `4px` | Seek bar track height |
| `--mj-player-radius` | `var(--mj-radius-md)` | Corner radius of the media container |
| `--mj-player-transcript-height` | `12rem` | Height of the transcript panel |
| `--mj-player-transcript-bg` | `var(--mj-color-surface-1)` | Transcript panel background |
| `--mj-player-active-cue-color` | `var(--mj-color-primary)` | Highlight color for active transcript cue |

## 10. States

- **idle** — media not yet started; poster shown; play button visible.
- **playing** — media playing; controls may auto-hide after 3s for video.
- **paused** — media paused; controls visible.
- **buffering** — `waiting` event on media; seek bar shows buffered ranges; spinner overlaid.
- **ended** — playback complete; replay button replaces play button.
- **error** — media error; error message shown in place of media.
- **captions-on** — active text track selected; captions visible over video.
- **transcript-open** — transcript panel expanded.
- **muted** — volume icon shows muted glyph.
- **fullscreen** — fullscreen button switches to exit-fullscreen glyph; controls always visible.

## 11. Behavior & interactions

The native `<video>` or `<audio>` element is created in the shadow DOM. `<source>`
and `<track>` elements placed in the default slot are moved into the native media
element via slot assignment in `connectedCallback`. This preserves SSR markup while
giving the component control of the media element.

Controls auto-hide after 3 seconds of no pointer/keyboard activity during video
playback; they reappear immediately on pointer move, pointer enter, or any key
press. Audio controls never auto-hide. Controls always remain visible when focus
is within the control bar.

The seek bar is a native `<input type="range">` styled with `::part(seek)`. Its
`aria-valuetext` is updated to a human-readable time string on every `input` event.

Captions: when `<track kind="subtitles|captions">` elements are slotted, the
captions button becomes active. Clicking it cycles through available tracks (or
toggles the single track on/off). The active `TextTrack.mode` is set to `"showing"`.

Transcript: when `show-transcript` is set, the component reads `VTTCue` text from
the active caption track and renders the cues as a list. The currently active cue
is scrolled into view and highlighted. If a custom `transcript` slot is provided,
the auto-generated panel is suppressed.

Autoplay is blocked when `prefers-reduced-motion: reduce` is active; the attribute
is accepted but a console warning is logged.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Space` / `K` | Toggle play / pause |
| `←` | Seek backward 5 seconds |
| `→` | Seek forward 5 seconds |
| `↑` | Increase volume by 10% |
| `↓` | Decrease volume by 10% |
| `M` | Toggle mute |
| `F` | Toggle fullscreen (video only) |
| `C` | Toggle captions |
| `Home` | Seek to beginning |
| `End` | Seek to end |
| `0`–`9` | Seek to 0%–90% of duration |
| `Tab` | Move focus to next control within the control bar |
| `Shift+Tab` | Move focus to previous control |
| `Esc` | Exit fullscreen (when in fullscreen mode) |

## 13. Accessibility

- The player is wrapped in a `<section>` with `aria-label` equal to the `label`
  attribute; this creates a landmark region for the player.
- The play/pause button has `aria-label` "Play" / "Pause" and updates on state change.
- The seek bar has `aria-label="Seek"`, `aria-valuemin="0"`, `aria-valuemax` set to
  `duration`, and `aria-valuenow`/`aria-valuetext` updated continuously.
- The captions button has `aria-pressed` set to `true`/`false`.
- The transcript panel is a `<div role="log" aria-live="polite">` that scrolls to
  the active cue; the active cue has `aria-current="true"`.
- During buffering a `<div role="status" aria-live="polite">` announces "Buffering…";
  on playback resume it announces "Playback resumed".
- All control buttons meet the 24×24 px minimum target size.
- The player is listed in the page's tab order; focus within the control bar is
  managed with a roving tabindex. Focus returns to the play button after leaving
  the control bar.
- Captions text uses forced-colors-aware styling and is not conveyed by color alone.

## 14. Form participation

N/A — `<mj-media-player>` does not contribute a form value.

## 15. Internationalization & RTL

- All user-facing strings (button labels, time format, error messages) are
  overridable via the localization hook (§3.8); defaults are English.
- Time display uses `Intl.DateTimeFormat` formatting conventions for the locale.
- In RTL mode, seek-bar fill direction and control bar layout order are reversed
  via logical CSS properties; arrow-key seek direction remains unchanged (left =
  backward, right = forward, per media player convention).
- Speed label and caption track labels respect the document's `lang` attribute.

## 16. Progressive enhancement / SSR

The server renders `<mj-media-player src="..."><source ...><track ...></mj-media-player>`.
Before the script loads the browser displays nothing (custom element not upgraded).
A `<noscript>` block inside the tag should contain a native `<video controls>` or
a link to download the file. On upgrade the component takes over the slotted
sources without re-requesting them.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — all visual values.
- **Focus utilities** (§6) — roving tabindex within control bar.
- **Live-region service** (§6) — buffering and playback announcements.
- **Localization hook** (§6) — all user-facing strings.
- **`<mj-image>`** — poster slot rendering.

## 18. Edge cases & error handling

- `src` is absent and no `<source>` elements slotted: shows empty state with an
  informative message.
- Media element fires `error`: replaces the media with an error panel; fires
  `mj-error`; does not rethrow.
- `show-transcript` set but no caption track available: transcript panel shows
  "No transcript available" message.
- Fullscreen request rejected (permissions policy): fullscreen button is hidden;
  console warning logged.
- Playback rate set outside the `playbackRates` list: clamped to nearest available
  value.
- `autoplay` + `prefers-reduced-motion: reduce`: autoplay suppressed; poster shown.
- Duration is `Infinity` (live stream): time display shows "Live"; seek bar hidden.

## 19. Acceptance criteria

- [ ] `type="video"` renders `<video>`; `type="audio"` renders `<audio>`.
- [ ] Play/pause button toggles native media; `mj-play` and `mj-pause` events fire.
- [ ] Seek bar reflects current time; dragging it updates `currentTime`; `mj-seek` fires.
- [ ] Volume control adjusts volume and mute; `mj-volume-change` fires.
- [ ] All keyboard shortcuts in §12 work correctly.
- [ ] Captions button activates slotted `<track>` elements; `mj-captions-change` fires.
- [ ] Transcript panel auto-scrolls to active cue; cue has `aria-current="true"`.
- [ ] `label` attribute populates the section `aria-label`.
- [ ] Buffering state shows spinner and announces "Buffering…" via live region.
- [ ] Controls auto-hide after 3s during video play; reappear on interaction.
- [ ] Autoplay is suppressed when `prefers-reduced-motion: reduce` is active.
- [ ] Fullscreen button requests/exits fullscreen; `F` key works.
- [ ] Error state is displayed; `mj-error` event fires on media error.
- [ ] Automated accessibility checks pass with no violations.
- [ ] `<source>` and `<track>` slots are forwarded to native media without re-request.

## 20. Open questions

- Should chapter markers (from `<track kind="chapters">`) be rendered as visual
  segments on the seek bar?
- Should the speed control be a `<mj-select>` (for consistency) or a custom
  inline segmented button group?
- Should picture-in-picture be exposed as a button in the control bar where
  the API is available?
