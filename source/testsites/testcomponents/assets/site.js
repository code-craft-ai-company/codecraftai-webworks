/*
 * site.js
 *
 * Page chrome shared by every page of the testcomponents site: the header
 * theme toggle, accessible tabs (every [data-tabs] tablist, each scoped to
 * its own tabs and panels) and the client-side filter of the landing pages.
 * Plain JavaScript; it does not use the component library under test.
 *
 * It must never contain a closing script tag (it is inlined into HTML).
 */

(function () {
  "use strict"

  /* ----- theme toggle ------------------------------------------------- */

  const themeButton = document.getElementById("theme-toggle")
  if (themeButton !== null) {
    themeButton.addEventListener("click", () => {
      const root = document.documentElement
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark"
      root.setAttribute("data-theme", next)
      themeButton.textContent = next === "dark" ? "Light theme" : "Dark theme"
      themeButton.setAttribute("aria-pressed", next === "dark" ? "true" : "false")
      document.dispatchEvent(new CustomEvent("site-theme-change", { detail: { theme: next } }))
    })
  }


  /* ----- tabs ------------------------------------------------------------ */

  function wireTablist(tablist) {
    const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'))
    if (tabs.length === 0) {
      return
    }
    function select(tab) {
      for (const candidate of tabs) {
        const selected = candidate === tab
        candidate.setAttribute("aria-selected", selected === true ? "true" : "false")
        candidate.tabIndex = selected === true ? 0 : -1
        const panel = document.getElementById(candidate.getAttribute("aria-controls"))
        if (panel !== null) {
          panel.hidden = selected === false
        }
      }
      tab.dispatchEvent(new CustomEvent("tabselect", { bubbles: true }))
      return
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => select(tab))
      tab.addEventListener("keydown", (event) => {
        let next = null
        if (event.key === "ArrowRight") {
          next = tabs[(index + 1) % tabs.length]
        } else if (event.key === "ArrowLeft") {
          next = tabs[(index - 1 + tabs.length) % tabs.length]
        } else if (event.key === "Home") {
          next = tabs[0]
        } else if (event.key === "End") {
          next = tabs[tabs.length - 1]
        }
        if (next === null) {
          return
        }
        event.preventDefault()
        select(next)
        next.focus()
      })
    })
    return
  }

  for (const tablist of document.querySelectorAll("[data-tabs]")) {
    wireTablist(tablist)
  }


  /* ----- landing-page filter -------------------------------------------- */

  const filter = document.getElementById("catalog-filter")
  if (filter !== null) {
    const cards = Array.from(document.querySelectorAll("[data-search]"))
    const sections = Array.from(document.querySelectorAll("[data-filter-section]"))
    const status = document.getElementById("filter-status")
    const empty = document.getElementById("filter-empty")

    function applyFilter() {
      const words = filter.value.trim().toLowerCase().split(/\s+/).filter((word) => word !== "")
      let shown = 0
      for (const card of cards) {
        const haystack = card.getAttribute("data-search")
        let matches = true
        for (const word of words) {
          if (haystack.indexOf(word) === -1) {
            matches = false
          }
        }
        card.hidden = matches === false
        if (matches === true) {
          shown += 1
        }
      }
      for (const section of sections) {
        const visible = section.querySelector("[data-search]:not([hidden])") !== null
        section.hidden = visible === false
      }
      if (status !== null) {
        status.textContent = words.length === 0 ? "" : shown + " of " + cards.length + " shown"
      }
      if (empty !== null) {
        empty.hidden = shown > 0
      }
      const url = new URL(location.href)
      if (filter.value.trim() === "") {
        url.searchParams.delete("q")
      } else {
        url.searchParams.set("q", filter.value.trim())
      }
      history.replaceState(null, "", url.toString())
      return
    }

    filter.addEventListener("input", applyFilter)
    filter.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && filter.value !== "") {
        filter.value = ""
        applyFilter()
      }
    })
    document.addEventListener("keydown", (event) => {
      const typing = event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement
      if (event.key === "/" && typing === false) {
        event.preventDefault()
        filter.focus()
      }
    })

    const initial = new URL(location.href).searchParams.get("q")
    if (initial !== null && initial !== "") {
      filter.value = initial
      applyFilter()
    }
  }
})()
