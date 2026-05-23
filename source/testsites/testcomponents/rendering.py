"""
    rendering.py

    Server-side HTML rendering for the testcomponents site. Builds the
    shared page chrome, the browse-by-group landing page, the per-group
    index pages, and the interactive per-component test pages.

    Pages load the mj-* component library and design tokens from the
    /static mount, so every component on a page is the real, live element.
"""

import html

from testcomponents.catalog import CATALOG
from testcomponents.catalog import component_for
from testcomponents.catalog import group_components
from testcomponents.catalog import total_component_count
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.groups import GROUP_ORDER
from testcomponents.catalog.groups import group_by_key


# Per-group accent colors -- give each group section and its cards a
# distinct accent so the browse page reads at a glance.
_GROUP_ACCENTS = {
    "selection": "#2563eb",
    "text": "#0891b2",
    "buttons": "#7c3aed",
    "navigation": "#0d9488",
    "layout": "#ca8a04",
    "feedback": "#dc2626",
    "overlays": "#db2777",
    "data": "#3949c4",
    "media": "#ea580c",
    "productivity": "#16a34a",
    "charts": "#4f46e5",
}


def _accent_for(group_key: str) -> str:
    """
        Return the accent color for a group.

        :param group_key: The group key.

        :returns: A CSS color string.
    """

    color = _GROUP_ACCENTS.get(group_key, "#2563eb")
    return color


# Site stylesheet, inlined into the page shell so the site is self-contained.
_SITE_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0; line-height: 1.55;
  font-family: var(--mj-font-sans, system-ui, sans-serif);
  color: var(--mj-text, #14181f);
  background: var(--mj-bg, #fff);
}
a { color: var(--mj-accent, #2563eb); text-decoration: none; }
a:hover { text-decoration: underline; }

header.site {
  display: flex; align-items: center; gap: 1rem;
  padding: 0.7rem 1.5rem;
  background: color-mix(in srgb, var(--mj-surface, #fff) 86%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--mj-border, #e0e3e9);
  position: sticky; top: 0; z-index: 50;
}
header.site .brand {
  display: flex; align-items: center; gap: 0.6rem; flex: 1;
  font-weight: 700; font-size: 1.05rem; color: inherit;
}
header.site .brand:hover { text-decoration: none; }
header.site .brand .mark {
  width: 1.6rem; height: 1.6rem; border-radius: 7px; flex: none;
  background: linear-gradient(135deg,
    var(--mj-color-accent-400, #4d83f7), var(--mj-color-accent-800, #122f78));
  box-shadow: var(--mj-elevation-1, 0 1px 2px rgba(20,24,31,0.2));
}
header.site .count {
  color: var(--mj-text-muted, #6b7280); font-size: 0.78rem; font-weight: 600;
  padding: 0.22rem 0.65rem; border-radius: 999px;
  background: var(--mj-bg-muted, #eef0f3);
}
.theme-toggle {
  font: inherit; font-size: 0.84rem; cursor: pointer;
  padding: 0.4rem 0.9rem; border-radius: 999px;
  border: 1px solid var(--mj-border-strong, #c7ccd6);
  background: var(--mj-surface, #fff); color: inherit;
  transition: border-color 120ms ease, color 120ms ease;
}
.theme-toggle:hover { border-color: var(--mj-accent, #2563eb); color: var(--mj-accent, #2563eb); }

/* Header toggle between the Components and Charts landing pages. */
.view-toggle {
  display: inline-flex; padding: 2px; border-radius: 999px;
  background: var(--mj-bg-muted, #eef0f3);
  border: 1px solid var(--mj-border, #e0e3e9);
}
.view-toggle .view-link {
  font-size: 0.82rem; font-weight: 600; text-decoration: none;
  padding: 0.32rem 0.85rem; border-radius: 999px;
  color: var(--mj-text-muted, #6b7280);
}
.view-toggle .view-link:hover { color: var(--mj-accent, #2563eb); }
.view-toggle .view-link.active {
  background: var(--mj-surface, #fff); color: var(--mj-accent, #2563eb);
  box-shadow: var(--mj-elevation-1, 0 1px 2px rgba(20, 24, 31, 0.08));
}

main { max-width: 1140px; margin: 0 auto; padding: 1.5rem 1.5rem 5rem; }
h1 { font-size: 1.7rem; letter-spacing: -0.015em; }

.hero {
  margin: 0.25rem 0 2.25rem; padding: 2.6rem 2.2rem; border-radius: 18px;
  color: #fff;
  background:
    radial-gradient(circle at 14% 16%,
      color-mix(in srgb, var(--mj-color-accent-300, #80a8ff) 42%, transparent), transparent 55%),
    radial-gradient(circle at 88% 12%,
      color-mix(in srgb, var(--mj-color-accent-900, #0d2256) 55%, transparent), transparent 52%),
    linear-gradient(135deg,
      var(--mj-color-accent-600, #1d4fc4), var(--mj-color-accent-900, #0d2256));
  box-shadow: var(--mj-elevation-3, 0 8px 24px rgba(20,24,31,0.18));
}
.hero h1 { margin: 0 0 0.55rem; font-size: 2.15rem; letter-spacing: -0.025em; }
.hero p { margin: 0; max-width: 62ch; opacity: 0.92; }
.hero .stats { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1.5rem; }
.hero .stat {
  font-size: 0.83rem; font-weight: 600; padding: 0.35rem 0.85rem; border-radius: 999px;
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25);
}

.crumbs { font-size: 0.82rem; color: var(--mj-text-muted, #6b7280); margin-bottom: 0.75rem; }
.crumbs a { color: var(--mj-text-muted, #6b7280); }

.group-section { margin: 2.25rem 0; }
.group-section > h2 {
  display: flex; align-items: baseline; gap: 0.5rem;
  font-size: 1.15rem; margin: 0 0 0.35rem;
  padding-left: 0.7rem;
  border-left: 4px solid var(--group-accent, var(--mj-accent, #2563eb));
}
.group-section > h2 a { color: inherit; }
.group-section > h2 .count { font-size: 0.8rem; font-weight: 400; color: var(--mj-text-muted, #6b7280); }
.group-section > .cs { margin: 0 0 0.9rem 0.85rem; font-size: 0.9rem; color: var(--mj-text-muted, #6b7280); }

.card-grid {
  display: grid; gap: 0.85rem;
  grid-template-columns: repeat(auto-fill, minmax(232px, 1fr));
}
.card {
  position: relative; overflow: hidden;
  display: block; padding: 1rem 1.1rem; color: inherit;
  border: 1px solid var(--mj-border, #e0e3e9);
  border-radius: 13px;
  background: var(--mj-surface, #fff);
  transition: transform 130ms ease, box-shadow 130ms ease, border-color 130ms ease;
}
.card::before {
  content: ""; position: absolute; inset: 0 auto 0 0; width: 3px;
  background: var(--group-accent, var(--mj-accent, #2563eb));
  opacity: 0; transition: opacity 130ms ease;
}
.card:hover {
  transform: translateY(-3px); text-decoration: none;
  border-color: var(--group-accent, var(--mj-accent, #2563eb));
  box-shadow: var(--mj-elevation-2, 0 2px 8px rgba(20,24,31,0.12));
}
.card:hover::before { opacity: 1; }
.card .tag {
  font-family: var(--mj-font-mono, monospace); font-size: 0.74rem;
  color: var(--group-accent, var(--mj-accent, #2563eb));
}
.card .ct { font-weight: 700; margin: 0.28rem 0 0.2rem; font-size: 0.98rem; }
.card .cs { font-size: 0.83rem; color: var(--mj-text-muted, #6b7280); }

.section-label {
  font-weight: 700; font-size: 0.74rem; text-transform: uppercase;
  letter-spacing: 0.07em; color: var(--mj-accent, #2563eb);
  margin: 1.9rem 0 0.6rem;
}
.doc-body {
  border: 1px solid var(--mj-border, #e0e3e9); border-radius: 13px;
  padding: 0.4rem 1.15rem; background: var(--mj-surface, #fff);
}
h1 .count {
  font-family: var(--mj-font-mono, monospace); font-size: 0.95rem; font-weight: 500;
  color: var(--mj-accent, #2563eb);
  background: var(--mj-color-accent-50, #eef4ff);
  padding: 0.15rem 0.5rem; border-radius: 7px; vertical-align: middle;
}

table.meta {
  border-collapse: collapse; width: 100%; font-size: 0.88rem;
  border: 1px solid var(--mj-border, #e0e3e9); border-radius: 11px; overflow: hidden;
}
table.meta thead th {
  background: var(--mj-bg-subtle, #f7f8fa); color: var(--mj-text-muted, #6b7280);
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;
}
table.meta th, table.meta td {
  text-align: left; padding: 0.5rem 0.7rem;
  border-bottom: 1px solid var(--mj-border, #e0e3e9);
}
table.meta tbody tr:last-child td { border-bottom: 0; }
code {
  font-family: var(--mj-font-mono, monospace); font-size: 0.88em;
  background: var(--mj-bg-muted, #eef0f3); padding: 0.1rem 0.36rem; border-radius: 5px;
}
pre.code {
  background: #0d2236; color: #e7edf5;
  border-radius: 13px; padding: 1rem 1.15rem; overflow: auto;
  font-family: var(--mj-font-mono, monospace); font-size: 0.84rem; line-height: 1.55;
}
pre.code code { background: none; padding: 0; color: inherit; font-size: inherit; }

/* Lead description -- kept at the top of the component page, height-capped
   so the demo controls below it stay at a predictable, in-viewport spot. */
.lead {
  margin: 0.35rem 0 1.1rem; font-size: 0.95rem;
  max-height: 7.5em; overflow: auto;
}
.lead > :first-child { margin-top: 0; }
.lead > :last-child { margin-bottom: 0; }

/* Tabbed Example / Play demo section. */
.demo {
  border: 1px solid var(--mj-border, #e0e3e9); border-radius: 14px;
  background: var(--mj-surface, #fff); overflow: hidden;
}
.demo-bar {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  background: var(--mj-bg-subtle, #f7f8fa);
  border-bottom: 1px solid var(--mj-border, #e0e3e9);
}
.tablist { display: flex; gap: 0.25rem; flex: 1; }
.tablist [role="tab"] {
  font: inherit; font-size: 0.86rem; font-weight: 600; cursor: pointer;
  padding: 0.4rem 1rem; border: 0; border-radius: 8px;
  background: transparent; color: var(--mj-text-muted, #6b7280);
}
.tablist [role="tab"]:hover { background: var(--mj-bg-muted, #eef0f3); }
.tablist [role="tab"][aria-selected="true"] {
  background: var(--mj-surface, #fff); color: var(--mj-accent, #2563eb);
  box-shadow: inset 0 -2px 0 var(--mj-accent, #2563eb);
}
[role="tabpanel"] { padding: 0.85rem; }
[role="tabpanel"][hidden] { display: none; }
.panel-hint { margin: 0 0 0.6rem; font-size: 0.82rem; color: var(--mj-text-muted, #6b7280); }

.scenario-frame, .pg-preview {
  display: block; width: 100%;
  border: 1px solid var(--mj-border, #e0e3e9); border-radius: 10px;
  background-color: var(--mj-bg, #fff);
}
.scenario-frame { min-height: 320px; }
.pg-preview {
  min-height: 240px;
  background-image:
    linear-gradient(45deg, var(--mj-bg-subtle, #f7f8fa) 25%, transparent 25%),
    linear-gradient(-45deg, var(--mj-bg-subtle, #f7f8fa) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, var(--mj-bg-subtle, #f7f8fa) 75%),
    linear-gradient(-45deg, transparent 75%, var(--mj-bg-subtle, #f7f8fa) 75%);
  background-size: 18px 18px;
  background-position: 0 0, 0 9px, 9px -9px, -9px 0;
}

.pg-actions { display: flex; gap: 0.5rem; flex: none; }
.pg-actions button {
  font: inherit; font-size: 0.84rem; font-weight: 600; cursor: pointer;
  padding: 0.4rem 0.95rem; border-radius: 8px;
  border: 1px solid var(--mj-border-strong, #c7ccd6);
  background: var(--mj-surface, #fff); color: inherit;
  transition: border-color 120ms ease, transform 80ms ease;
}
.pg-actions button:hover { border-color: var(--mj-accent, #2563eb); }
.pg-actions button:active { transform: translateY(1px); }
.pg-actions button.primary {
  background: var(--mj-accent, #2563eb); color: #fff; border-color: var(--mj-accent, #2563eb);
}

/* HTML + Style editors, shown below the component view in the Play tab. */
.pg-code {
  display: grid; gap: 0.7rem; grid-template-columns: 1fr 1fr; margin-top: 0.7rem;
}
@media (max-width: 820px) { .pg-code { grid-template-columns: 1fr; } }
.pg-pane { display: flex; flex-direction: column; min-width: 0; }
.pg-pane label {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--mj-text-muted, #6b7280); margin-bottom: 0.3rem;
}
.pg-pane textarea {
  width: 100%; min-height: 108px; resize: vertical;
  font-family: var(--mj-font-mono, monospace); font-size: 0.8rem; line-height: 1.5;
  padding: 0.65rem; color: inherit;
  border: 1px solid var(--mj-border-strong, #c7ccd6); border-radius: 9px;
  background: var(--mj-bg-subtle, #f7f8fa);
}
.pg-pane textarea:focus { outline: 2px solid var(--mj-accent, #2563eb); outline-offset: 1px; }
"""


# Playground controller script. Builds an isolated preview document from the
# HTML editor and the Style (CSS) editor and renders it into the preview
# iframe. Isolation matters: components such as modal dialogs make their host
# document inert, which would otherwise disable the playground controls. The
# iframe also executes any <script> in the example, so data-driven components
# (charts, tables) populate correctly. The read-only Example scenario iframe
# is rendered once from the initial example.
_PLAYGROUND_JS = (
    "(function () {\n"
    "  var code = document.getElementById('pg-code');\n"
    "  var styleEl = document.getElementById('pg-style');\n"
    "  var frame = document.getElementById('pg-frame');\n"
    "  var exampleFrame = document.getElementById('example-frame');\n"
    "  var runBtn = document.getElementById('pg-run');\n"
    "  var resetBtn = document.getElementById('pg-reset');\n"
    "  if (code === null || frame === null) { return; }\n"
    "  var initialHtml = code.value;\n"
    "  var initialStyle = styleEl !== null ? styleEl.value : '';\n"
    "  var OPEN = '<scr' + 'ipt type=\"module\" src=\"/static/javascript/index.js\">';\n"
    "  var CLOSE = '<' + '/scr' + 'ipt>';\n"
    "  function docFor(markup, css) {\n"
    "    var theme = document.documentElement.getAttribute('data-theme') || 'light';\n"
    "    return '<!DOCTYPE html><html data-theme=\"' + theme + '\"><head>'\n"
    "      + '<meta charset=\"utf-8\">'\n"
    "      + '<link rel=\"stylesheet\" href=\"/static/styles/tokens.css\">'\n"
    "      + '<link rel=\"stylesheet\" href=\"/static/styles/base.css\">'\n"
    "      + OPEN + CLOSE\n"
    "      + '<style>body{font-family:var(--mj-font-sans,sans-serif);'\n"
    "      + 'color:var(--mj-text,#14181f);background:var(--mj-bg,#fff);'\n"
    "      + 'padding:1rem;margin:0;}' + (css || '') + '</style>'\n"
    "      + '</head><body>' + markup + '</body></html>';\n"
    "  }\n"
    "  function run() {\n"
    "    var css = styleEl !== null ? styleEl.value : '';\n"
    "    frame.setAttribute('srcdoc', docFor(code.value, css));\n"
    "  }\n"
    "  if (runBtn !== null) { runBtn.addEventListener('click', run); }\n"
    "  if (resetBtn !== null) {\n"
    "    resetBtn.addEventListener('click', function () {\n"
    "      code.value = initialHtml;\n"
    "      if (styleEl !== null) { styleEl.value = initialStyle; }\n"
    "      run();\n"
    "    });\n"
    "  }\n"
    "  run();\n"
    "  if (exampleFrame !== null) {\n"
    "    exampleFrame.setAttribute('srcdoc', docFor(initialHtml, ''));\n"
    "  }\n"
    "})();\n"
)


# Tab controller for the Example / Play demo section. Plain accessible tabs
# (tablist / tab / tabpanel) so the page chrome does not depend on the
# component library under test.
_TABS_JS = (
    "(function () {\n"
    "  var tabs = Array.prototype.slice.call("
    "document.querySelectorAll('[role=tab]'));\n"
    "  if (tabs.length === 0) { return; }\n"
    "  function select(tab) {\n"
    "    tabs.forEach(function (t) {\n"
    "      var on = t === tab;\n"
    "      t.setAttribute('aria-selected', on ? 'true' : 'false');\n"
    "      t.tabIndex = on ? 0 : -1;\n"
    "      var panel = document.getElementById(t.getAttribute('aria-controls'));\n"
    "      if (panel !== null) { panel.hidden = !on; }\n"
    "    });\n"
    "  }\n"
    "  tabs.forEach(function (tab, index) {\n"
    "    tab.addEventListener('click', function () { select(tab); });\n"
    "    tab.addEventListener('keydown', function (event) {\n"
    "      var delta = 0;\n"
    "      if (event.key === 'ArrowRight') { delta = 1; }\n"
    "      else if (event.key === 'ArrowLeft') { delta = -1; }\n"
    "      else { return; }\n"
    "      event.preventDefault();\n"
    "      var next = tabs[(index + delta + tabs.length) % tabs.length];\n"
    "      select(next);\n"
    "      next.focus();\n"
    "    });\n"
    "  });\n"
    "})();\n"
)


# Theme toggle script, shared by every page.
_THEME_JS = """
(function () {
  var btn = document.getElementById('theme-toggle');
  if (btn === null) { return; }
  btn.addEventListener('click', function () {
    var root = document.documentElement;
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    btn.textContent = next === 'dark' ? 'Light theme' : 'Dark theme';
  });
})();
"""


def _view_toggle(active_view: str) -> str:
    """
        Render the header toggle that switches between the Components
        landing page and the Charts landing page.

        :param active_view: "components" or "charts" -- the active side.

        :returns: HTML for the toggle control.
    """

    components_active = active_view == "components"
    charts_active = active_view == "charts"

    components_class = "view-link active" if components_active else "view-link"
    charts_class = "view-link active" if charts_active else "view-link"
    components_aria = ' aria-current="page"' if components_active else ""
    charts_aria = ' aria-current="page"' if charts_active else ""

    toggle = f"""<div class="view-toggle" data-testid="view-toggle" role="group" aria-label="Views">
      <a href="/" class="{components_class}" data-testid="view-link-components"{components_aria}>Components</a>
      <a href="/charts" class="{charts_class}" data-testid="view-link-charts"{charts_aria}>Charts</a>
    </div>"""
    return toggle


def page_shell(
    title: str,
    body_html: str,
    extra_js: str = "",
    active_view: str = "components",
) -> str:
    """
        Wrap page body content in the full HTML document shell.

        :param title: The page title.
        :param body_html: The inner HTML for the <main> region.
        :param extra_js: Optional page-specific JavaScript.
        :param active_view: Which header view link is current --
            "components" or "charts".

        :returns: A complete HTML document string.
    """

    safe_title = html.escape(title)
    count = total_component_count()
    toggle = _view_toggle(active_view)

    document = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} &middot; mj-* Test Components</title>
  <link rel="stylesheet" href="/static/styles/tokens.css">
  <link rel="stylesheet" href="/static/styles/base.css">
  <script type="module" src="/static/javascript/index.js"></script>
  <style>{_SITE_CSS}</style>
</head>
<body>
  <header class="site">
    <a class="brand" href="/" data-testid="site-brand"><span class="mark" aria-hidden="true"></span>mj-* Test Components</a>
    {toggle}
    <span class="count" data-testid="component-count">{count} components</span>
    <button class="theme-toggle" id="theme-toggle" data-testid="theme-toggle">Dark theme</button>
  </header>
  <main data-testid="main">
{body_html}
  </main>
  <script>{_THEME_JS}</script>
  <script>{extra_js}</script>
</body>
</html>
"""
    return document


def render_browse_page() -> str:
    """
        Render the landing page that browses all components by group.

        :returns: The complete HTML document for the browse page.
    """

    total = total_component_count()
    group_count = len(GROUP_ORDER)

    sections = []
    sections.append(
        f"""
    <div class="hero">
      <h1 data-testid="browse-heading">Browse Components by Group</h1>
      <p>An interactive test site for the automojo-webworks
        <code>mj-*</code> web component library. Pick a group, then a
        component, to read its documentation and experiment with it live
        in an editable playground.</p>
      <div class="stats">
        <span class="stat">{total} components</span>
        <span class="stat">{group_count} groups</span>
        <span class="stat">Themeable &middot; Accessible &middot; Dockable</span>
      </div>
    </div>"""
    )

    for group in GROUP_ORDER:
        components = group_components(group.key)
        safe_title = html.escape(group.title)
        safe_desc = html.escape(group.description)
        accent = _accent_for(group.key)

        cards = []
        for doc in components:
            cards.append(_component_card(group.key, doc))
        cards_html = "\n".join(cards)

        section = f"""
    <section class="group-section" data-testid="group-{group.key}"
      style="--group-accent: {accent}">
      <h2><a href="/components/{group.key}" data-testid="group-link-{group.key}">{safe_title}</a>
        <span class="count">{len(components)} components</span></h2>
      <p class="cs">{safe_desc}</p>
      <div class="card-grid">
{cards_html}
      </div>
    </section>"""
        sections.append(section)

    body = "\n".join(sections)
    document = page_shell(title="Browse", body_html=body, active_view="components")
    return document


# The data-visualization components that live in the `media` group but belong
# on the dedicated Charts page alongside the `charts` group.
_CHART_MEDIA_TAGS = ("mj-chart", "mj-map", "mj-gauge", "mj-sparkline", "mj-diagram")


def _chart_docs() -> "list[tuple[str, ComponentDoc]]":
    """
        Collect every chart component as (group_key, doc): the whole
        `charts` group plus the data-visualization components from `media`.

        :returns: A list of (group_key, ComponentDoc) pairs.
    """

    docs = []
    for doc in group_components("charts"):
        docs.append(("charts", doc))
    for doc in group_components("media"):
        if doc.tag in _CHART_MEDIA_TAGS:
            docs.append(("media", doc))

    return docs


def _view_for(group_key: str, tag: "str | None" = None) -> str:
    """
        Decide which header view ("components" or "charts") a group or
        component page belongs to.

        :param group_key: The group key of the page.
        :param tag: The component tag, when on a component page.

        :returns: "charts" for chart pages, otherwise "components".
    """

    if group_key == "charts":
        return "charts"
    if tag is not None and tag in _CHART_MEDIA_TAGS:
        return "charts"

    return "components"


def render_charts_page() -> str:
    """
        Render the dedicated Charts landing page: the project/SCM chart
        components plus the data-visualization components from `media`.

        :returns: The complete HTML document for the charts page.
    """

    docs = _chart_docs()
    chart_total = len(docs)

    project_cards = []
    viz_cards = []
    for group_key, doc in docs:
        card = _component_card(group_key, doc)
        if group_key == "charts":
            project_cards.append(card)
        else:
            viz_cards.append(card)

    project_html = "\n".join(project_cards)
    viz_html = "\n".join(viz_cards)

    body = f"""
    <div class="hero">
      <h1 data-testid="charts-heading">Charts &amp; Visualizations</h1>
      <p>The interactive, data-driven chart components of the
        automojo-webworks <code>mj-*</code> library. Every chart accepts
        JSON data, redraws dynamically when its data changes, and emits
        interaction events.</p>
      <div class="stats">
        <span class="stat">{chart_total} charts</span>
        <span class="stat">JSON-driven &middot; SVG</span>
        <span class="stat">Interactive &middot; Dynamic</span>
      </div>
    </div>

    <section class="group-section" data-testid="charts-section-project"
      style="--group-accent: #4f46e5">
      <h2>Project, Schedule &amp; SCM Charts
        <span class="count">{len(project_cards)} charts</span></h2>
      <p class="cs">Branch graphs, pipelines, Gantt, roadmaps and planning charts.</p>
      <div class="card-grid" data-testid="charts-cards-project">
{project_html}
      </div>
    </section>

    <section class="group-section" data-testid="charts-section-viz"
      style="--group-accent: #ea580c">
      <h2>Data Visualizations
        <span class="count">{len(viz_cards)} charts</span></h2>
      <p class="cs">General-purpose charts, gauges, sparklines, maps and diagrams.</p>
      <div class="card-grid" data-testid="charts-cards-viz">
{viz_html}
      </div>
    </section>

{_render_chart_library_section()}"""

    document = page_shell(title="Charts", body_html=body, active_view="charts")
    return document


def _render_chart_library_section() -> str:
    """
        Render the comprehensive Chart Library gallery -- one card per
        catalogued <mj-chart type="..."> chart type, grouped by category.

        :returns: HTML for the gallery sections.
    """

    from testcomponents.charttypes import (
        chart_types_by_category,
        chart_type_count,
        CHART_CATEGORIES,
    )

    grouped = chart_types_by_category()
    total = chart_type_count()

    sections = []
    sections.append(
        f"""
    <section class="group-section" data-testid="chart-library-intro"
      style="--group-accent: #2563eb">
      <h2>Chart Library
        <span class="count">{total} chart types</span></h2>
      <p class="cs">The comprehensive set of chart types served by the
        <code>&lt;mj-chart&gt;</code> controller. Every type below is the
        same controller configured with a different <code>type</code>
        attribute and SVG renderer.</p>
    </section>"""
    )

    for key, title, accent in CHART_CATEGORIES:
        types = grouped.get(key, [])
        if len(types) == 0:
            continue
        cards = []
        for doc in types:
            safe_type = html.escape(doc.type_key)
            safe_title = html.escape(doc.title)
            safe_summary = html.escape(doc.summary)
            cards.append(
                f"""        <a class="card" href="/chart-type/{safe_type}"
          data-testid="chart-type-card-{safe_type}">
          <span class="tag">type="{safe_type}"</span>
          <div class="ct">{safe_title}</div>
          <div class="cs">{safe_summary}</div>
        </a>"""
            )
        cards_html = "\n".join(cards)
        safe_cat_title = html.escape(title)
        sections.append(
            f"""
    <section class="group-section" data-testid="chart-category-{key}"
      style="--group-accent: {accent}">
      <h3 style="font-size:1.05rem;margin:0 0 0.6rem;padding-left:0.7rem;
        border-left:4px solid {accent}">{safe_cat_title}
        <span class="count">{len(types)} types</span></h3>
      <div class="card-grid" data-testid="chart-category-cards-{key}">
{cards_html}
      </div>
    </section>"""
        )

    body = "\n".join(sections)
    return body


def render_chart_type_page(type_key: str) -> "str | None":
    """
        Render the playground page for one <mj-chart> chart type.

        :param type_key: The chart type key.

        :returns: The complete HTML document, or None if unknown.
    """

    from testcomponents.charttypes import chart_type_for

    doc = chart_type_for(type_key)
    if doc is None:
        return None

    safe_type = html.escape(doc.type_key)
    safe_title = html.escape(doc.title)
    safe_summary = html.escape(doc.summary)
    safe_category = html.escape(doc.category)
    escaped_example = html.escape(doc.example)
    style_placeholder = "/* Optional: add CSS to restyle the chart, then press Run. */"
    escaped_style = html.escape(style_placeholder)

    body = f"""
    <div class="crumbs"><a href="/charts">Charts</a> /
      <a href="/charts">Chart Library</a> / {safe_title}</div>
    <h1 data-testid="chart-type-heading">{safe_title}
      <span class="count">type="{safe_type}"</span></h1>

    <div class="lead" data-testid="chart-type-summary">
      <p>{safe_summary}</p>
    </div>

    <section class="demo" data-testid="demo-section">
      <div class="demo-bar">
        <div class="tablist" role="tablist" aria-label="{safe_title} demo">
          <button type="button" role="tab" id="tab-example" data-testid="tab-example"
            aria-controls="panel-example" aria-selected="false" tabindex="-1">Example</button>
          <button type="button" role="tab" id="tab-play" data-testid="tab-play"
            aria-controls="panel-play" aria-selected="true" tabindex="0">Play</button>
        </div>
        <div class="pg-actions" data-testid="playground-controls">
          <button type="button" class="primary" id="pg-run"
            data-testid="playground-run">Run &#9654;</button>
          <button type="button" id="pg-reset"
            data-testid="playground-reset">Reset</button>
        </div>
      </div>

      <div role="tabpanel" id="panel-example" data-testid="panel-example"
        aria-labelledby="tab-example" hidden>
        <p class="panel-hint">The chart shown in a ready-made scenario.</p>
        <iframe class="scenario-frame" id="example-frame" data-testid="example-frame"
          title="{safe_title} example scenario"></iframe>
      </div>

      <div role="tabpanel" id="panel-play" data-testid="panel-play"
        aria-labelledby="tab-play">
        <iframe class="pg-preview" id="pg-frame" data-testid="playground-preview"
          title="Live {safe_title} preview"></iframe>
        <div class="pg-code">
          <div class="pg-pane">
            <label for="pg-code">HTML</label>
            <textarea id="pg-code" data-testid="playground-editor"
              spellcheck="false">{escaped_example}</textarea>
          </div>
          <div class="pg-pane">
            <label for="pg-style">Style (CSS)</label>
            <textarea id="pg-style" data-testid="playground-style-editor"
              spellcheck="false">{escaped_style}</textarea>
          </div>
        </div>
      </div>
    </section>

    <div class="section-label">Category</div>
    <div class="doc-body">{safe_category}</div>"""

    document = page_shell(
        title=doc.title,
        body_html=body,
        extra_js=_PLAYGROUND_JS + _TABS_JS,
        active_view="charts",
    )
    return document


def _component_card(group_key: str, doc: ComponentDoc) -> str:
    """
        Render a single component card linking to its test page.

        :param group_key: The owning group key.
        :param doc: The ComponentDoc to render.

        :returns: HTML for one card anchor.
    """

    safe_tag = html.escape(doc.tag)
    safe_title = html.escape(doc.title)
    safe_summary = html.escape(doc.summary)

    card = f"""        <a class="card" href="/components/{group_key}/{safe_tag}" data-testid="card-{safe_tag}">
          <span class="tag">&lt;{safe_tag}&gt;</span>
          <div class="ct">{safe_title}</div>
          <div class="cs">{safe_summary}</div>
        </a>"""
    return card


def render_group_index(group_key: str) -> "str | None":
    """
        Render the index page for a single group.

        :param group_key: The group key to render.

        :returns: The HTML document, or None if the group is unknown.
    """

    group = group_by_key(group_key)
    if group is None:
        return None

    components = group_components(group_key)
    safe_title = html.escape(group.title)
    safe_desc = html.escape(group.description)

    cards = []
    for doc in components:
        cards.append(_component_card(group_key, doc))
    cards_html = "\n".join(cards)

    accent = _accent_for(group_key)

    body = f"""
    <div class="group-section" style="--group-accent: {accent}">
      <div class="crumbs"><a href="/">Home</a> / {safe_title}</div>
      <h1 data-testid="group-heading"
        style="border-left:4px solid {accent};padding-left:0.7rem">{safe_title}</h1>
      <p class="cs">{safe_desc}</p>
      <div class="card-grid" data-testid="group-cards">
{cards_html}
      </div>
    </div>"""

    document = page_shell(
        title=group.title,
        body_html=body,
        active_view=_view_for(group_key),
    )
    return document


def _meta_table(rows: "list[tuple[str, str]]", label: str, testid: str) -> str:
    """
        Render an attributes/events metadata table.

        :param rows: List of (name, description) pairs.
        :param label: Column header for the name column.
        :param testid: data-testid value for the table.

        :returns: HTML for the table, or an empty string when no rows.
    """

    if len(rows) == 0:
        return ""

    body_rows = []
    for name, description in rows:
        safe_name = html.escape(name)
        safe_description = html.escape(description)
        body_rows.append(
            f"      <tr><td><code>{safe_name}</code></td><td>{safe_description}</td></tr>"
        )
    rows_html = "\n".join(body_rows)

    table = f"""    <table class="meta" data-testid="{testid}">
      <thead><tr><th>{html.escape(label)}</th><th>Description</th></tr></thead>
      <tbody>
{rows_html}
      </tbody>
    </table>"""
    return table


_STYLE_PLACEHOLDER = (
    "/* Optional: add CSS here to restyle the component, then press Run.\n"
    "   e.g.  mj-button { margin: 8px; }  */"
)


def render_component_page(group_key: str, tag: str) -> "str | None":
    """
        Render the interactive test/documentation page for one component.

        Page layout (top to bottom):
          1. Heading and the component description.
          2. A tabbed demo section -- an "Example" tab showing the
             component in a ready-made scenario, and a "Play" tab with the
             live sandbox: the component preview above its editable HTML
             and Style code.
          3. How-to guidance, then the attribute and event tables.

        The demo controls (tabs, Run, Reset) sit high on the page so they
        stay within the viewport without scrolling while tests run.

        :param group_key: The owning group key.
        :param tag: The component tag.

        :returns: The HTML document, or None if the component is unknown.
    """

    doc = component_for(group_key, tag)
    if doc is None:
        return None

    group = group_by_key(group_key)
    safe_group_title = html.escape(group.title)
    safe_tag = html.escape(doc.tag)
    safe_title = html.escape(doc.title)

    attrs_table = _meta_table(doc.attributes, "Attribute", "attributes-table")
    events_table = _meta_table(doc.events, "Event", "events-table")

    escaped_example = html.escape(doc.example)
    escaped_style = html.escape(_STYLE_PLACEHOLDER)

    body = f"""
    <div class="crumbs"><a href="/">Home</a> /
      <a href="/components/{group_key}">{safe_group_title}</a> / {safe_tag}</div>
    <h1 data-testid="component-heading">{safe_title}
      <span class="count">&lt;{safe_tag}&gt;</span></h1>

    <div class="lead" data-testid="component-description">{doc.description}</div>

    <section class="demo" data-testid="demo-section">
      <div class="demo-bar">
        <div class="tablist" role="tablist" aria-label="{safe_title} demo">
          <button type="button" role="tab" id="tab-example" data-testid="tab-example"
            aria-controls="panel-example" aria-selected="false" tabindex="-1">Example</button>
          <button type="button" role="tab" id="tab-play" data-testid="tab-play"
            aria-controls="panel-play" aria-selected="true" tabindex="0">Play</button>
        </div>
        <div class="pg-actions" data-testid="playground-controls">
          <button type="button" class="primary" id="pg-run"
            data-testid="playground-run">Run &#9654;</button>
          <button type="button" id="pg-reset"
            data-testid="playground-reset">Reset</button>
        </div>
      </div>

      <div role="tabpanel" id="panel-example" data-testid="panel-example"
        aria-labelledby="tab-example" hidden>
        <p class="panel-hint">The component shown in a ready-made scenario.</p>
        <iframe class="scenario-frame" id="example-frame" data-testid="example-frame"
          title="{safe_title} example scenario"></iframe>
      </div>

      <div role="tabpanel" id="panel-play" data-testid="panel-play"
        aria-labelledby="tab-play">
        <iframe class="pg-preview" id="pg-frame" data-testid="playground-preview"
          title="Live {safe_title} preview"></iframe>
        <div class="pg-code">
          <div class="pg-pane">
            <label for="pg-code">HTML</label>
            <textarea id="pg-code" data-testid="playground-editor"
              spellcheck="false">{escaped_example}</textarea>
          </div>
          <div class="pg-pane">
            <label for="pg-style">Style (CSS)</label>
            <textarea id="pg-style" data-testid="playground-style-editor"
              spellcheck="false">{escaped_style}</textarea>
          </div>
        </div>
      </div>
    </section>

    <div class="section-label">How to use it</div>
    <div class="doc-body" data-testid="component-howto">{doc.how_to_use}</div>

    {_optional_block(attrs_table, "Attributes")}
    {_optional_block(events_table, "Events")}"""

    document = page_shell(
        title=doc.title,
        body_html=body,
        extra_js=_PLAYGROUND_JS + _TABS_JS,
        active_view=_view_for(group_key, tag),
    )
    return document


def _optional_block(table_html: str, label: str) -> str:
    """
        Wrap a metadata table with a section label when it is non-empty.

        :param table_html: The rendered table HTML (may be empty).
        :param label: The section label text.

        :returns: The labelled block, or an empty string.
    """

    if table_html == "":
        return ""

    block = f'<div class="section-label">{html.escape(label)}</div>\n{table_html}'
    return block
