/*
 * sanitize.js
 *
 * The allow-list HTML sanitizer every component uses for markup it did not
 * write itself: the rich text editor's value and pasted content, the
 * markdown preview, code-highlighter output and chat message bodies.
 *
 * Usage:
 *   import { sanitizeHtml, sanitizeHtmlToFragment } from "../core/sanitize.js";
 *   element.innerHTML = sanitizeHtml(untrusted)
 *   element.replaceChildren(sanitizeHtmlToFragment(untrusted, { allowedTags: ["b", "a"] }))
 */

import { safeUrl, safeLinkUrl } from "./html.js";

/* Tags the rich text editor can produce and accepts back. */
export const RICH_TEXT_ALLOWED_TAGS = [
  "b", "i", "u", "s", "em", "strong", "a", "ul", "ol", "li",
  "h1", "h2", "h3", "h4", "blockquote", "pre", "code", "br", "p"
];

/* Attributes kept per tag. Every attribute that is not listed is removed. */
export const RICH_TEXT_ALLOWED_ATTRIBUTES = {
  a: ["href", "title"]
};

/*
 * Elements rewritten to an allowed equivalent instead of being unwrapped, so
 * the markup browsers generate while editing (a <div> per line, <strike>)
 * keeps its meaning in the stored value.
 */
export const RICH_TEXT_TAG_ALIASES = {
  div: "p",
  strike: "s",
  del: "s"
};

/* Elements removed together with everything inside them. */
const DISCARDED_TAGS = [
  "script", "style", "iframe", "frame", "frameset", "object", "embed", "applet",
  "template", "noscript", "noembed", "noframes", "xmp", "plaintext", "title",
  "textarea", "select", "option", "optgroup", "head", "meta", "link", "base",
  "svg", "math", "audio", "video", "source", "track", "canvas", "portal"
];

/*
 * Attributes whose value is a URL and must pass `safeUrl`. The ones a user
 * follows as a link must pass the stricter `safeLinkUrl` (no data: / blob:).
 */
const URL_ATTRIBUTES = ["href", "src", "cite", "poster", "action", "formaction", "background", "longdesc"];
const LINK_URL_ATTRIBUTES = ["href", "action", "formaction"];

/* A block-level child means a <div> cannot become a <p> without nesting blocks. */
const BLOCK_CHILD_SELECTOR = "p, div, ul, ol, li, h1, h2, h3, h4, h5, h6, blockquote, pre, table, hr";

const XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml";

function toLookup(names) {
  const lookup = {}
  for (let index = 0; index < names.length; index = index + 1) {
    lookup[String(names[index]).toLowerCase()] = true
  }
  return lookup
}

/*
 * Remove every attribute of `element` that is not on the allow-list for its
 * tag, and every URL attribute whose value `safeUrl` (`safeLinkUrl` for a
 * link target) rejects.
 */
function cleanAttributes(element, tagName, config) {
  const allowedForTag = config.allowedAttributes[tagName] || []
  const allowedForAll = config.allowedAttributes["*"] || []
  const attributes = Array.from(element.attributes)

  for (let index = 0; index < attributes.length; index = index + 1) {
    const attribute = attributes[index]
    const name = attribute.name.toLowerCase()

    let keep = allowedForTag.indexOf(name) !== -1 || allowedForAll.indexOf(name) !== -1

    /* Event handlers and inline styles are never kept, whatever the list says. */
    if (name.startsWith("on") === true || name === "style" || name === "srcdoc") {
      keep = false
    }

    if (keep === true && URL_ATTRIBUTES.indexOf(name) !== -1) {
      const isLink = LINK_URL_ATTRIBUTES.indexOf(name) !== -1
      const checked = isLink === true ? safeLinkUrl(attribute.value, null) : safeUrl(attribute.value, null)
      if (checked === null) {
        keep = false
      }
    }

    if (keep === false) {
      element.removeAttribute(attribute.name)
    }
  }
  return
}

/*
 * Sanitize the children of `parent` in place. A disallowed element is
 * unwrapped only after its own subtree has been sanitized, so the children
 * hoisted into `parent` have always been checked.
 */
function cleanChildren(parent, config, inertDocument) {
  let child = parent.firstChild

  while (child !== null) {
    const next = child.nextSibling

    if (child.nodeType === Node.TEXT_NODE) {
      /* Text is kept; the serializer escapes it. */
    } else if (child.nodeType !== Node.ELEMENT_NODE) {
      /* Comments, processing instructions, CDATA. */
      parent.removeChild(child)
    } else {
      const tagName = child.localName.toLowerCase()
      const foreign = child.namespaceURI !== XHTML_NAMESPACE

      if (foreign === true || config.discarded[tagName] === true) {
        parent.removeChild(child)
      } else if (config.allowed[tagName] === true) {
        cleanAttributes(child, tagName, config)
        if (tagName === "a" && config.linkRel !== null) {
          child.setAttribute("rel", config.linkRel)
        }
        cleanChildren(child, config, inertDocument)
      } else {
        cleanChildren(child, config, inertDocument)

        const alias = config.aliases[tagName]
        const canAlias = alias !== undefined && config.allowed[alias] === true &&
          child.querySelector(BLOCK_CHILD_SELECTOR) === null

        if (canAlias === true) {
          const replacement = inertDocument.createElement(alias)
          while (child.firstChild !== null) {
            replacement.appendChild(child.firstChild)
          }
          parent.replaceChild(replacement, child)
        } else {
          while (child.firstChild !== null) {
            parent.insertBefore(child.firstChild, child)
          }
          parent.removeChild(child)
        }
      }
    }

    child = next
  }
  return
}

/* Build the sanitizer configuration from the caller's options. */
function buildConfig(options) {
  const settings = options || {}
  const config = {
    allowed: toLookup(settings.allowedTags || RICH_TEXT_ALLOWED_TAGS),
    allowedAttributes: settings.allowedAttributes || RICH_TEXT_ALLOWED_ATTRIBUTES,
    aliases: settings.aliases || RICH_TEXT_TAG_ALIASES,
    discarded: toLookup(DISCARDED_TAGS),
    linkRel: typeof settings.linkRel === "string" ? settings.linkRel : null
  }
  return config
}

/*
 * Parse `markup` into a separate, inert document and sanitize its body in
 * place. Returns the body, or null when there is no markup.
 */
function sanitizeIntoInertBody(markup, options) {
  let body = null

  if (markup !== null && markup !== undefined && String(markup).length > 0) {
    const config = buildConfig(options)
    const parser = new DOMParser()
    const inertDocument = parser.parseFromString(
      `<!DOCTYPE html><html><head></head><body>${String(markup)}</body></html>`,
      "text/html"
    )
    cleanChildren(inertDocument.body, config, inertDocument)
    body = inertDocument.body
  }

  return body
}

/*
 * Return `markup` reduced to an allow-list of elements and attributes, as a
 * string.
 *
 * The markup is parsed by DOMParser into a separate, inert document: scripts
 * do not run, images do not load and event-handler attributes never fire
 * there. Nothing is ever assigned to `innerHTML` of a node of the live
 * document before it has been sanitized.
 *
 * options:
 *   allowedTags        array of tag names kept (default: the rich text set)
 *   allowedAttributes  { tag: [names], "*": [names] } kept per tag
 *   aliases            { from: to } elements renamed instead of unwrapped
 *   linkRel            when set, every kept <a> gets this `rel` value
 *                      (for example "noopener noreferrer")
 */
export function sanitizeHtml(markup, options) {
  const body = sanitizeIntoInertBody(markup, options)
  const sanitized = body !== null ? body.innerHTML : ""
  return sanitized
}

/*
 * Like `sanitizeHtml`, but return a DocumentFragment of the live document.
 * The sanitized nodes are imported (cloned) from the inert document, so the
 * result is never re-parsed as HTML in the page. Prefer it when the result is
 * inserted into the DOM right away.
 */
export function sanitizeHtmlToFragment(markup, options) {
  const fragment = document.createDocumentFragment()
  const body = sanitizeIntoInertBody(markup, options)

  if (body !== null) {
    const children = Array.from(body.childNodes)
    for (let index = 0; index < children.length; index = index + 1) {
      fragment.appendChild(document.importNode(children[index], true))
    }
  }

  return fragment
}
