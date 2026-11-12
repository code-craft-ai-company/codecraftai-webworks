/*
 * html.js
 *
 * Escaping helpers for markup that components assign to `innerHTML`.
 *
 * Every value that did not originate as a literal in the component source --
 * attribute values, child text, data items, URLs -- must pass through one of
 * these helpers before it is placed in a markup string. A value that a server
 * escaped correctly arrives here already decoded by the HTML parser, so
 * interpolating it raw turns it back into live markup.
 *
 *   escapeHtml(value)   text or attribute-value context (always quote attributes)
 *   safeUrl(value)      href / src context; rejects script-bearing schemes
 *   safeLinkUrl(value)  href of untrusted links; also refuses data: and blob:
 *   html`...${value}`   template tag that escapes every interpolation
 *   raw(markup)         marks markup the component built itself as trusted
 *
 * Usage:
 *   const markup = html`<a class="item" href="${safeUrl(item.url)}">${item.label}</a>`
 *   const list = html`<ul>${items.map((item) => html`<li>${item.name}</li>`)}</ul>`
 */

const ESCAPE_PATTERN = /[&<>"'`]/g;

const ESCAPE_MAP = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  "\"": "&quot;",
  "'": "&#39;",
  "`": "&#96;"
};

/* URL schemes a component may place in href / src without review. */
const SAFE_URL_SCHEMES = ["http:", "https:", "mailto:", "tel:", "sms:", "blob:"];

/* data: URLs are accepted only for these inert image types. */
const SAFE_DATA_URL_PATTERN = /^data:image\/(png|gif|jpeg|jpg|webp|avif|bmp);/i;

/*
 * Markup that has already been escaped or was assembled from escaped parts.
 * Instances come only from `html` and `raw`, so a plain string can never be
 * mistaken for trusted markup.
 */
class TrustedMarkup {
  constructor(markup) {
    this.markup = markup
  }

  toString() {
    return this.markup
  }
}

/*
 * Escape a value for an HTML text node or a quoted attribute value.
 * `null` and `undefined` become the empty string.
 */
export function escapeHtml(value) {
  let escaped = ""

  if (value !== null && value !== undefined) {
    const text = String(value)
    escaped = text.replace(ESCAPE_PATTERN, (character) => {
      return ESCAPE_MAP[character]
    })
  }

  return escaped
}

/* Alias that reads better at attribute call sites. */
export function escapeAttr(value) {
  const escaped = escapeHtml(value)
  return escaped
}

/*
 * Return `value` when it is a URL a component may navigate to or load, and
 * `fallback` (default "#") otherwise. Relative URLs, fragments and the schemes
 * in SAFE_URL_SCHEMES pass; `javascript:`, `vbscript:` and non-image `data:`
 * URLs do not. The result still needs `escapeHtml` when placed in markup --
 * the `html` tag does that for you.
 */
export function safeUrl(value, fallback) {
  const rejected = fallback !== undefined ? fallback : "#"
  let result = rejected

  if (value !== null && value !== undefined) {
    /* Browsers ignore control characters and leading spaces inside a scheme. */
    const text = String(value)
    const compact = text.replace(/[\u0000- \u007f-\u009f]/g, "")
    const schemeMatch = compact.match(/^([a-zA-Z][a-zA-Z0-9+.-]*):/)

    if (schemeMatch === null) {
      result = text
    } else {
      const scheme = `${schemeMatch[1].toLowerCase()}:`
      if (SAFE_URL_SCHEMES.indexOf(scheme) >= 0) {
        result = text
      } else if (scheme === "data:" && SAFE_DATA_URL_PATTERN.test(compact) === true) {
        result = text
      }
    }
  }

  return result
}

/*
 * Return `value` when it is a URL an untrusted LINK may navigate to, and
 * `fallback` (default "#") otherwise. Stricter than `safeUrl`: besides the
 * script-bearing schemes it refuses every `data:` and `blob:` URL, since a
 * link (unlike an image source) opens them as a document. Use it for hrefs
 * that come from user content (messages, comments, pasted markup).
 */
export function safeLinkUrl(value, fallback) {
  const rejected = fallback !== undefined ? fallback : "#"
  let result = safeUrl(value, rejected)

  if (result !== rejected) {
    const compact = String(result).replace(/[\u0000- \u007f-\u009f]/g, "").toLowerCase()
    if (compact.startsWith("data:") === true || compact.startsWith("blob:") === true) {
      result = rejected
    }
  }

  return result
}

/*
 * Mark markup as trusted so `html` inserts it verbatim. Use only for strings
 * the component assembled itself from escaped parts or literals.
 */
export function raw(markup) {
  const text = markup !== null && markup !== undefined ? String(markup) : ""
  const trusted = new TrustedMarkup(text)
  return trusted
}

function renderValue(value) {
  let rendered = ""

  if (value instanceof TrustedMarkup) {
    rendered = value.markup
  } else if (Array.isArray(value) === true) {
    const parts = []
    for (let index = 0; index < value.length; index = index + 1) {
      parts.push(renderValue(value[index]))
    }
    rendered = parts.join("")
  } else if (value === false || value === true) {
    /* Booleans render nothing so `${condition && html`...`}` works. */
    rendered = ""
  } else {
    rendered = escapeHtml(value)
  }

  return rendered
}

/*
 * Template tag: every interpolated value is escaped unless it is the result
 * of another `html` call or of `raw()`. Arrays are rendered item by item.
 * The result is a TrustedMarkup; `String(result)` (or assigning it to
 * `innerHTML`) yields the markup.
 */
export function html(strings, ...values) {
  const parts = []

  for (let index = 0; index < strings.length; index = index + 1) {
    parts.push(strings[index])
    if (index < values.length) {
      parts.push(renderValue(values[index]))
    }
  }

  const trusted = new TrustedMarkup(parts.join(""))
  return trusted
}
