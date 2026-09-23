/*
 * intl.js
 *
 * Localization and locale-aware formatting hook. Components read user-facing
 * default strings through `t()` and format numbers/dates/currency through the
 * helpers here, all built on the platform Intl APIs. Consumers can override
 * the locale and string table without rebuilding components.
 */

let currentLocale = (typeof navigator !== "undefined" && navigator.language) || "en";

/*
 * The default (English) string table. Every key a component passes to `t()`
 * must be registered here: `t()` returns the key itself on a miss, so an
 * unregistered key renders as raw text such as "mj.pagination.next" and the
 * `t(key) || "fallback"` pattern some components use never reaches its
 * fallback. `{name}` tokens are filled from the `params` argument of `t()`.
 */
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
  "core.search": "Search",

  "mj.appBar.navLabel": "Main",
  "mj.appBar.openNav": "Open navigation",
  "mj.appBar.closeNav": "Close navigation",
  "mj.appShell.navLabel": "Primary navigation",
  "mj.appShell.inspectorLabel": "Inspector",
  "mj.breadcrumb.navLabel": "Breadcrumb",
  "mj.breadcrumb.expand": "Show {count} hidden breadcrumbs",
  "mj.link.externalLabel": "opens in a new tab",
  "mj.pagination.navLabel": "Pagination",
  "mj.pagination.previous": "Previous",
  "mj.pagination.next": "Next",
  "mj.pagination.pageLabel": "Page {page}",
  "mj.pagination.currentPageLabel": "Page {page}, current",
  "mj.pagination.pageOf": "Page {page} of {total}",
  "mj.pagination.summary": "Showing {from}–{to} of {total}",
  "mj.select.noOptions": "No options",
  "mj.sideNav.navLabel": "Navigation",
  "mj.sideNav.collapse": "Collapse navigation",
  "mj.skipLink.label": "Skip to main content",
  "mj.toc.navLabel": "On this page",
  "mj.toc.empty": "No sections found",
  "mj.treeNav.navLabel": "Navigation",
  "mj.wizard.label": "Wizard",
  "mj.wizard.next": "Next",
  "mj.wizard.back": "Back",
  "mj.wizard.submit": "Submit"
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
