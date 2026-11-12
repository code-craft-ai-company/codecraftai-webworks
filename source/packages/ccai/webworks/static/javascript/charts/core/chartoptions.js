/*
 * chartoptions.js
 *
 * Shared readers for renderer option attributes on <mj-chart>. Every
 * renderer reads its boolean options through these so the attribute forms
 * mean the same thing on every chart type:
 *
 *   <mj-chart notched>                 true   (bare attribute)
 *   <mj-chart notched="">              true
 *   <mj-chart notched="true">          true
 *   <mj-chart notched="false">         false
 *   (attribute absent)                 the renderer's fallback (often a
 *                                      data field or a type default)
 *
 * Tri-state options (`markers="auto|true|false"`) use autoBooleanOption,
 * which also reads a bare attribute as true.
 */

function _isFalseWord(value) {
  /*
   * Whether an attribute value switches a boolean option off.
   *
   * :param value: The attribute value (a string).
   * :returns: true for "false" (any case, surrounding space ignored).
   */
  const word = String(value).trim().toLowerCase()
  const isFalse = word === "false"
  return isFalse
}


export function booleanOption(ctx, name, fallback) {
  /*
   * Read a boolean option attribute. A present attribute is true unless its
   * value is "false", so <mj-chart show-points>,
   * show-points="" and show-points="true" all switch the option on.
   *
   * :param ctx: The renderer context (its `attrs(name, fallback)` reads the
   *     host attribute).
   * :param name: The attribute name.
   * :param fallback: The value when the attribute is absent; anything other
   *     than `true` reads as false.
   * :returns: true or false.
   */
  let enabled = fallback === true
  const value = ctx.attrs(name, null)
  if (value !== null && value !== undefined) {
    enabled = _isFalseWord(value) === false
  }
  return enabled
}


export function autoBooleanOption(ctx, name) {
  /*
   * Read a tri-state option attribute ("auto" | "true" | "false"). A bare
   * attribute reads as true, like booleanOption; an absent attribute or the
   * value "auto" leaves the decision to the renderer.
   *
   * :param ctx: The renderer context.
   * :param name: The attribute name.
   * :returns: true, false or "auto".
   */
  let state = "auto"
  const value = ctx.attrs(name, null)
  if (value !== null && value !== undefined) {
    const word = String(value).trim().toLowerCase()
    if (word === "auto") {
      state = "auto"
    } else {
      state = _isFalseWord(word) === false
    }
  }
  return state
}
