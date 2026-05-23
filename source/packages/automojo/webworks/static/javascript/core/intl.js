/*
 * intl.js
 *
 * Localization and locale-aware formatting hook. Components read user-facing
 * default strings through `t()` and format numbers/dates/currency through the
 * helpers here, all built on the platform Intl APIs. Consumers can override
 * the locale and string table without rebuilding components.
 */

let currentLocale = (typeof navigator !== "undefined" && navigator.language) || "en";

const STRINGS = {
  "core.clear": "Clear",
  "core.close": "Close",
  "core.loading": "Loading",
  "core.noResults": "No results",
  "core.required": "This field is required.",
  "core.selectAll": "Select all",
  "core.previous": "Previous",
  "core.next": "Next",
  "core.expand": "Expand",
  "core.collapse": "Collapse",
  "core.remove": "Remove",
  "core.search": "Search"
};

const overrides = {};

export function setLocale(locale) {
  currentLocale = locale
  return
}

export function getLocale() {
  return currentLocale
}

/*
 * Resolve a localized string by key. `params` values replace {name} tokens.
 */
export function t(key, params) {
  let template = overrides[key]
  if (template === undefined) {
    template = STRINGS[key]
  }
  if (template === undefined) {
    template = key
  }

  let result = template
  if (params !== null && params !== undefined) {
    const names = Object.keys(params)
    for (let index = 0; index < names.length; index = index + 1) {
      const name = names[index]
      const token = `{${name}}`
      result = result.split(token).join(String(params[name]))
    }
  }
  return result
}

/* Register or override localized strings. */
export function registerStrings(table) {
  const keys = Object.keys(table)
  for (let index = 0; index < keys.length; index = index + 1) {
    const key = keys[index]
    overrides[key] = table[key]
  }
  return
}

export function formatNumber(value, options) {
  const formatter = new Intl.NumberFormat(currentLocale, options || {})
  const formatted = formatter.format(value)
  return formatted
}

export function formatCurrency(value, currency) {
  const formatter = new Intl.NumberFormat(currentLocale, {
    style: "currency",
    currency: currency || "USD"
  })
  const formatted = formatter.format(value)
  return formatted
}

export function formatDate(value, options) {
  const date = value instanceof Date ? value : new Date(value)
  const formatter = new Intl.DateTimeFormat(currentLocale, options || { dateStyle: "medium" })
  const formatted = formatter.format(date)
  return formatted
}

export function formatRelativeTime(value, unit) {
  const formatter = new Intl.RelativeTimeFormat(currentLocale, { numeric: "auto" })
  const formatted = formatter.format(value, unit || "day")
  return formatted
}
