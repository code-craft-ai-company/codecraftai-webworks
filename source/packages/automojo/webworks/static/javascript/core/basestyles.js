/*
 * basestyles.js
 *
 * Builds the shared base CSSStyleSheet adopted into every mj-* component's
 * shadow root by MjElement. The CSS is embedded as a string so the library
 * works with no network fetch and no build step (file:// and SSR safe).
 *
 * This is the canonical mirror of static/styles/base.css -- keep the two in
 * sync. The .css file exists for direct light-DOM linking; this module is for
 * shadow-root adoption (constructable stylesheets cannot be linked).
 */

const BASE_CSS = `
:host {
  box-sizing: border-box;
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
  line-height: var(--mj-line-height);
  color: var(--mj-text);
}
:host *, :host *::before, :host *::after { box-sizing: border-box; }
:host([hidden]), [hidden] { display: none !important; }
:host([disabled]) { pointer-events: none; cursor: not-allowed; }

:host([anchor]) { position: absolute; z-index: var(--mj-layer-docked); }
:host([anchor="top-start"])    { inset-block-start: var(--mj-anchor-inset,0); inset-inline-start: var(--mj-anchor-inset,0); }
:host([anchor="top"])          { inset-block-start: var(--mj-anchor-inset,0); inset-inline-start: 50%; translate: -50% 0; }
:host([anchor="top-end"])      { inset-block-start: var(--mj-anchor-inset,0); inset-inline-end: var(--mj-anchor-inset,0); }
:host([anchor="start"])        { inset-inline-start: var(--mj-anchor-inset,0); inset-block-start: 50%; translate: 0 -50%; }
:host([anchor="center"])       { inset-block-start: 50%; inset-inline-start: 50%; translate: -50% -50%; }
:host([anchor="end"])          { inset-inline-end: var(--mj-anchor-inset,0); inset-block-start: 50%; translate: 0 -50%; }
:host([anchor="bottom-start"]) { inset-block-end: var(--mj-anchor-inset,0); inset-inline-start: var(--mj-anchor-inset,0); }
:host([anchor="bottom"])       { inset-block-end: var(--mj-anchor-inset,0); inset-inline-start: 50%; translate: -50% 0; }
:host([anchor="bottom-end"])   { inset-block-end: var(--mj-anchor-inset,0); inset-inline-end: var(--mj-anchor-inset,0); }
:host([anchor="stretch"])      { inset: var(--mj-anchor-inset,0); }

:host([dock]) { flex: 0 0 auto; }
:host([dock="fill"]) { flex: 1 1 auto; min-width: 0; min-height: 0; }

.mj-visually-hidden {
  position: absolute !important;
  width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}
.mj-focus-ring:focus-visible, :host(:focus-visible) {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
:host(:focus:not(:focus-visible)) { outline: none; }

@media (prefers-reduced-motion: reduce) {
  :host, :host * {
    animation-duration: 1ms !important;
    transition-duration: 1ms !important;
    scroll-behavior: auto !important;
  }
}
@media (forced-colors: active) {
  :host { --mj-border: CanvasText; --mj-focus-ring: Highlight; }
  .mj-focus-ring:focus-visible, :host(:focus-visible) { outline-color: Highlight; }
}
`;

function buildBaseSheet() {
  let sheet = null

  const supportsConstructable = typeof CSSStyleSheet === "function"
  if (supportsConstructable === true) {
    sheet = new CSSStyleSheet()
    sheet.replaceSync(BASE_CSS)
  }

  return sheet
}

export const sharedBaseSheet = buildBaseSheet();
