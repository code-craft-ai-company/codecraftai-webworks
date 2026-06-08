/*
 * registry.js
 *
 * Idempotent custom-element registration. Calling `define` more than once for
 * the same tag (e.g. the bundle is loaded twice) is a safe no-op rather than
 * a thrown DOMException.
 */

const registered = new Set();

/*
 * Register a component class. The class must expose a static `tagName`.
 * Returns the resolved tag name.
 */
export function define(componentClass) {
  const tag = componentClass.tagName

  if (tag === null || tag === undefined || tag.length === 0) {
    throw new Error("Component class is missing a static tagName")
  }

  const alreadyKnown = registered.has(tag) || customElements.get(tag) !== undefined
  if (alreadyKnown === true) {
    return tag
  }

  customElements.define(tag, componentClass)
  registered.add(tag)
  return tag
}

/* Register many component classes at once. */
export function defineAll(componentClasses) {
  const tags = []
  for (let index = 0; index < componentClasses.length; index = index + 1) {
    const tag = define(componentClasses[index])
    tags.push(tag)
  }
  return tags
}

/* Resolve when the given tag has been upgraded. */
export function whenDefined(tag) {
  const promise = customElements.whenDefined(tag)
  return promise
}
