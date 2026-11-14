"""
    rendering.py

    Server-side HTML rendering for the testcomponents site. Builds the
    shared page chrome, the browse-by-group landing page, the Charts
    landing page, the per-group index pages, and the sandbox pages for
    every component, chart type and chart part.

    The page chrome is plain HTML, CSS and vanilla JavaScript inlined into
    each page (assets/site.css, assets/site.js, assets/sandbox.js); it does
    not load the mj-* library it tests. The library is loaded only inside
    the sandbox preview documents, whose bootstrap is assets/preview.js.
"""

import html
import json
import os
import re

from ccai.errors.exceptions import SemanticError

from testcomponents.catalog import component_for
from testcomponents.catalog import component_neighbours
from testcomponents.catalog import group_components
from testcomponents.catalog import total_component_count
from testcomponents.catalog.attributedoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentexample import ComponentExample
from testcomponents.catalog.groups import GROUP_ORDER
from testcomponents.catalog.groups import group_by_key


# ---------------------------------------------------------------------------
# Inlined assets
# ---------------------------------------------------------------------------

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Text that would end or derail the element an asset is inlined into.
_FORBIDDEN_IN_SCRIPT = ("</script", "<script", "<!--")
_FORBIDDEN_IN_STYLE = ("</style",)


def _read_asset(name: str, forbidden: "tuple[str, ...]") -> str:
    """
        Read an asset file that is inlined into every page.

        :param name: The file name under ``assets/``.
        :param forbidden: Substrings the asset must not contain (case-insensitive).

        :returns: The file text.

        :raises SemanticError: When the asset contains a forbidden substring.
    """

    path = os.path.join(_ASSETS_DIR, name)
    with open(path, "r", encoding="utf-8") as asset_file:
        text = asset_file.read()

    lowered = text.lower()
    for needle in forbidden:
        if needle in lowered:
            errmsg = "The inlined asset {} must not contain {!r}; split the literal.".format(
                path, needle)
            raise SemanticError(errmsg)

    return text


_SITE_CSS = _read_asset("site.css", _FORBIDDEN_IN_STYLE)
_SITE_JS = _read_asset("site.js", _FORBIDDEN_IN_SCRIPT)
_SANDBOX_JS = _read_asset("sandbox.js", _FORBIDDEN_IN_SCRIPT)
_PREVIEW_BOOT_JS = _read_asset("preview.js", _FORBIDDEN_IN_SCRIPT)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

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

_TAG_PATTERN = re.compile(r"<[^>]*>")
_BACKTICK_PATTERN = re.compile(r"`([^`]+)`")


def _accent_for(group_key: str) -> str:
    """
        Return the accent color for a group.

        :param group_key: The group key.

        :returns: A CSS color string.
    """

    color = _GROUP_ACCENTS.get(group_key, "#2563eb")
    return color


def _reference_text(text: str) -> str:
    """
        Render a plain-text reference cell: entities are decoded, the text is
        escaped, and `backticked` words become code.

        :param text: The plain text from the catalog.

        :returns: Safe HTML.
    """

    decoded = html.unescape(text)
    escaped = html.escape(decoded)
    rendered = _BACKTICK_PATTERN.sub(r"<code>\1</code>", escaped)
    return rendered


def _plain_paragraphs(text: str) -> str:
    """
        Render a plain-text description as paragraphs: a blank line starts a
        new paragraph and each paragraph is rendered by :func:`_reference_text`.

        :param text: The plain text from the catalog.

        :returns: Safe HTML, one ``<p>`` per paragraph ("" for blank text).
    """

    paragraphs = []
    for block in re.split(r"\n\s*\n", text.strip()):
        collapsed = " ".join(block.split())
        if collapsed != "":
            paragraphs.append(f"<p>{_reference_text(collapsed)}</p>")

    rendered = "\n".join(paragraphs)
    return rendered


def _search_text(*parts: str) -> str:
    """
        Build the lower-case text a landing-page card is filtered by.

        :param parts: Tag, title, summary (summary may hold HTML).

        :returns: The text, escaped for an attribute value.
    """

    pieces = []
    for part in parts:
        stripped = _TAG_PATTERN.sub(" ", part)
        pieces.append(html.unescape(stripped))
    joined = " ".join(pieces)
    collapsed = " ".join(joined.lower().split())
    value = html.escape(collapsed, quote=True)
    return value


def _json_for_script(data: object) -> str:
    """
        Serialize data for a <script type="application/json"> element.

        :param data: JSON-serializable data.

        :returns: JSON text in which no character can end the element.
    """

    text = json.dumps(data, ensure_ascii=False)
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    text = text.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return text


def site_counts() -> "dict[str, int]":
    """
        Return the counts the site shows, derived from the catalogs in one place.

        :returns: Components, groups, chart types and chart parts.
    """

    from testcomponents.charttypes import chart_part_count
    from testcomponents.charttypes import chart_type_count

    counts = {
        "components": total_component_count(),
        "groups": len(GROUP_ORDER),
        "chart_types": chart_type_count(),
        "chart_parts": chart_part_count(),
    }
    return counts


def _plural(count: int, singular: str, plural: str) -> str:
    """
        Format a count with the right noun.

        :param count: The count.
        :param singular: The noun for one.
        :param plural: The noun for any other count.

        :returns: e.g. "1 component", "143 components".
    """

    noun = singular if count == 1 else plural
    text = "{} {}".format(count, noun)
    return text


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------

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

    toggle = f"""<nav class="view-toggle" data-testid="view-toggle" aria-label="Views">
      <a href="/" class="{components_class}" data-testid="view-link-components"{components_aria}>Components</a>
      <a href="/charts" class="{charts_class}" data-testid="view-link-charts"{charts_aria}>Charts</a>
    </nav>"""
    return toggle


def page_shell(
    title: str,
    body_html: str,
    extra_js: str = "",
    active_view: str = "components",
    main_class: str = "",
) -> str:
    """
        Wrap page body content in the full HTML document shell.

        :param title: The page title.
        :param body_html: The inner HTML for the <main> region.
        :param extra_js: Optional page-specific JavaScript.
        :param active_view: Which header view link is current --
            "components" or "charts".
        :param main_class: Optional class for <main> (``detail`` widens it).

        :returns: A complete HTML document string.
    """

    safe_title = html.escape(title)
    counts = site_counts()
    component_label = _plural(counts["components"], "component", "components")
    chart_label = _plural(counts["chart_types"], "chart type", "chart types")
    toggle = _view_toggle(active_view)
    main_attribute = f' class="{html.escape(main_class)}"' if main_class != "" else ""

    page_script = ""
    if extra_js != "":
        page_script = f"\n  <script>{extra_js}</script>"

    document = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} &middot; mj-* Test Components</title>
  <link rel="stylesheet" href="/static/styles/tokens.css">
  <link rel="stylesheet" href="/static/styles/base.css">
  <style>{_SITE_CSS}</style>
</head>
<body>
  <header class="site">
    <a class="brand" href="/" data-testid="site-brand"><span class="mark" aria-hidden="true"></span>mj-* Test Components</a>
    {toggle}
    <span class="counts">
      <span class="count" data-testid="component-count">{component_label}</span>
      <span class="count" data-testid="chart-type-count">{chart_label}</span>
    </span>
    <button type="button" class="theme-toggle" id="theme-toggle" data-testid="theme-toggle" aria-pressed="false">Dark theme</button>
  </header>
  <main data-testid="main"{main_attribute}>
{body_html}
  </main>
  <script>{_SITE_JS}</script>{page_script}
</body>
</html>
"""
    return document


def render_not_found(message: str) -> str:
    """
        Render the styled not-found page.

        :param message: The plain-text message; it is escaped.

        :returns: The complete HTML document.
    """

    safe_message = html.escape(message)
    body = f"""
    <h1 data-testid="not-found">Not found</h1>
    <p data-testid="not-found-message">{safe_message}</p>
    <p><a href="/">Return to the component browser</a> &middot; <a href="/charts">Charts</a></p>"""

    document = page_shell(title="Not found", body_html=body)
    return document


def _filter_bar(label: str, placeholder: str, empty_text: str) -> str:
    """
        Render the client-side filter of a landing page.

        :param label: The accessible label of the field.
        :param placeholder: The placeholder text.
        :param empty_text: The message shown when nothing matches.

        :returns: HTML for the filter bar and its empty-state message.
    """

    bar = f"""
    <div class="filter-bar" role="search">
      <label class="visually-hidden" for="catalog-filter">{html.escape(label)}</label>
      <input type="search" id="catalog-filter" data-testid="catalog-filter" autocomplete="off"
        placeholder="{html.escape(placeholder)}">
      <span class="filter-status" id="filter-status" data-testid="filter-status" aria-live="polite"></span>
      <span class="filter-status">Press <kbd>/</kbd> to filter</span>
    </div>
    <p class="filter-empty" id="filter-empty" data-testid="filter-empty" hidden>{html.escape(empty_text)}</p>"""
    return bar


# ---------------------------------------------------------------------------
# Landing pages
# ---------------------------------------------------------------------------

def _component_card(group_key: str, doc: ComponentDoc, href: "str | None" = None) -> str:
    """
        Render a single component card linking to its test page.

        :param group_key: The owning group key.
        :param doc: The ComponentDoc to render.
        :param href: The link target; default the component page.

        :returns: HTML for one card anchor.
    """

    safe_tag = html.escape(doc.tag)
    safe_title = html.escape(doc.title)
    if href is None:
        href = f"/components/{group_key}/{doc.tag}"
    safe_href = html.escape(href)
    search = _search_text(doc.tag, doc.title, doc.summary)

    card = f"""        <a class="card" href="{safe_href}" data-testid="card-{safe_tag}" data-search="{search}">
          <span class="tag">&lt;{safe_tag}&gt;</span>
          <div class="ct">{safe_title}</div>
          <div class="cs">{doc.summary}</div>
        </a>"""
    return card


def render_browse_page() -> str:
    """
        Render the landing page that browses all components by group.

        :returns: The complete HTML document for the browse page.
    """

    counts = site_counts()

    sections = []
    sections.append(
        f"""
    <div class="hero">
      <h1 data-testid="browse-heading">Browse Components by Group</h1>
      <p>An interactive sandbox for the codecraftai-webworks
        <code>mj-*</code> web component library. Pick a component to read
        its reference, switch between its examples, and try its attributes,
        slots, events, themes and text direction live.</p>
      <div class="stats">
        <span class="stat" data-testid="stat-components">{_plural(counts["components"], "component", "components")}</span>
        <span class="stat">{_plural(counts["groups"], "group", "groups")}</span>
        <span class="stat">Themeable &middot; Accessible &middot; Dockable</span>
      </div>
    </div>"""
    )
    sections.append(_filter_bar(
        label="Filter components",
        placeholder="Filter by tag, name or summary",
        empty_text="No component matches the filter.",
    ))

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
    <section class="group-section" data-testid="group-{group.key}" data-filter-section
      style="--group-accent: {accent}">
      <h2><a href="/components/{group.key}" data-testid="group-link-{group.key}">{safe_title}</a>
        <span class="count">{_plural(len(components), "component", "components")}</span></h2>
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
        components, the data-visualization components from `media`, the
        chart parts and the chart-type library.

        :returns: The complete HTML document for the charts page.
    """

    from testcomponents.charttypes import CHART_PARTS

    docs = _chart_docs()
    counts = site_counts()

    project_cards = []
    viz_cards = []
    for group_key, doc in docs:
        card = _component_card(group_key, doc)
        if group_key == "charts":
            project_cards.append(card)
        else:
            viz_cards.append(card)

    part_cards = []
    for doc in CHART_PARTS:
        part_cards.append(_component_card("chart-parts", doc, href=f"/chart-part/{doc.tag}"))

    project_html = "\n".join(project_cards)
    viz_html = "\n".join(viz_cards)
    parts_html = "\n".join(part_cards)
    chart_total = len(docs)

    filter_html = _filter_bar(
        label="Filter charts",
        placeholder="Filter charts by tag, type, name or summary",
        empty_text="No chart matches the filter.",
    )

    body = f"""
    <div class="hero">
      <h1 data-testid="charts-heading">Charts &amp; Visualizations</h1>
      <p>The interactive, data-driven chart components of the
        codecraftai-webworks <code>mj-*</code> library. Every chart accepts
        JSON data, redraws dynamically when its data changes, and emits
        interaction events.</p>
      <div class="stats">
        <span class="stat">{_plural(chart_total, "chart component", "chart components")}</span>
        <span class="stat" data-testid="stat-chart-types">{_plural(counts["chart_types"], "chart type", "chart types")}</span>
        <span class="stat">{_plural(counts["chart_parts"], "chart part", "chart parts")}</span>
      </div>
    </div>
{filter_html}

    <section class="group-section" data-testid="charts-section-project" data-filter-section
      style="--group-accent: #4f46e5">
      <h2>Project, Schedule &amp; SCM Charts
        <span class="count">{_plural(len(project_cards), "chart", "charts")}</span></h2>
      <p class="cs">Branch graphs, pipelines, Gantt, roadmaps and planning charts.</p>
      <div class="card-grid" data-testid="charts-cards-project">
{project_html}
      </div>
    </section>

    <section class="group-section" data-testid="charts-section-viz" data-filter-section
      style="--group-accent: #ea580c">
      <h2>Data Visualizations
        <span class="count">{_plural(len(viz_cards), "chart", "charts")}</span></h2>
      <p class="cs">General-purpose charts, gauges, sparklines, maps and diagrams.</p>
      <div class="card-grid" data-testid="charts-cards-viz">
{viz_html}
      </div>
    </section>

    <section class="group-section" data-testid="charts-section-parts" data-filter-section
      style="--group-accent: #0d9488">
      <h2>Chart parts
        <span class="count">{_plural(len(part_cards), "part", "parts")}</span></h2>
      <p class="cs">Title, legend and data table: components that bind to an
        <code>&lt;mj-chart&gt;</code> and can be placed anywhere on the page.</p>
      <div class="card-grid" data-testid="charts-cards-parts">
{parts_html}
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

    from testcomponents.charttypes import CHART_CATEGORIES
    from testcomponents.charttypes import chart_type_count
    from testcomponents.charttypes import chart_types_by_category

    grouped = chart_types_by_category()
    total = chart_type_count()

    sections = []
    sections.append(
        f"""
    <section class="group-section" data-testid="chart-library-intro"
      style="--group-accent: #2563eb">
      <h2>Chart Library
        <span class="count">{_plural(total, "chart type", "chart types")}</span></h2>
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
            # The summary is plain text (contract section 6).
            safe_summary = _reference_text(doc.summary)
            search = _search_text(doc.type_key, "mj-chart", doc.title, safe_summary, title)
            cards.append(
                f"""        <a class="card" href="/chart-type/{safe_type}"
          data-testid="chart-type-card-{safe_type}" data-search="{search}">
          <span class="tag">type="{safe_type}"</span>
          <div class="ct">{safe_title}</div>
          <div class="cs">{safe_summary}</div>
        </a>"""
            )
        cards_html = "\n".join(cards)
        safe_cat_title = html.escape(title)
        sections.append(
            f"""
    <section class="group-section" data-testid="chart-category-{key}" data-filter-section
      style="--group-accent: {accent}">
      <h3>{safe_cat_title}
        <span class="count">{_plural(len(types), "type", "types")}</span></h3>
      <div class="card-grid" data-testid="chart-category-cards-{key}">
{cards_html}
      </div>
    </section>"""
        )

    body = "\n".join(sections)
    return body


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


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------

def _table(testid: str, headers: "list[str]", rows: "list[list[str]]") -> str:
    """
        Render a reference table whose cells are already safe HTML.

        :param testid: data-testid value for the table.
        :param headers: The column headers (plain text).
        :param rows: The rows, one list of cell HTML per row.

        :returns: HTML for the table, or an empty string when there are no rows.
    """

    if len(rows) == 0:
        return ""

    header_cells = []
    for header in headers:
        header_cells.append(f"<th scope=\"col\">{html.escape(header)}</th>")
    header_html = "".join(header_cells)

    body_rows = []
    for row in rows:
        cells = []
        for cell in row:
            cells.append(f"<td>{cell}</td>")
        body_rows.append("      <tr>" + "".join(cells) + "</tr>")
    rows_html = "\n".join(body_rows)

    table = f"""    <div class="table-scroll"><table class="meta" data-testid="{testid}">
      <thead><tr>{header_html}</tr></thead>
      <tbody>
{rows_html}
      </tbody>
    </table></div>"""
    return table


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


def _attributes_table(attributes: "list[AttributeDoc]", testid: str) -> str:
    """
        Render the attributes (or chart options) table.

        :param attributes: The AttributeDoc entries.
        :param testid: data-testid value for the table.

        :returns: The table HTML, or "" when there are none.
    """

    any_typed = False
    for attribute in attributes:
        if attribute.typed is True:
            any_typed = True

    rows = []
    for attribute in attributes:
        name_cell = f"<code>{html.escape(attribute.name)}</code>"
        description_cell = _reference_text(attribute.description)
        if any_typed is True:
            if attribute.typed is True:
                kind_cell = html.escape(attribute.kind)
            else:
                kind_cell = '<span class="muted">&mdash;</span>'
            value_codes = []
            for value in attribute.values:
                value_codes.append(f"<code>{html.escape(value)}</code>")
            values_cell = " ".join(value_codes)
            if attribute.default is not None:
                default_cell = f"<code>{html.escape(attribute.default)}</code>"
            else:
                default_cell = ""
            rows.append([name_cell, kind_cell, values_cell, default_cell, description_cell])
        else:
            rows.append([name_cell, description_cell])

    if any_typed is True:
        headers = ["Attribute", "Kind", "Values", "Default", "Description"]
    else:
        headers = ["Attribute", "Description"]

    table = _table(testid, headers, rows)
    return table


def _pairs_table(
    rows: "list[tuple[str, str]]",
    label: str,
    testid: str,
    name_format: str = "{}",
) -> str:
    """
        Render a (name, description) reference table.

        :param rows: The (name, description) pairs.
        :param label: The name column header.
        :param testid: data-testid value for the table.
        :param name_format: Format applied to the name before it is shown.

        :returns: The table HTML, or "" when there are no rows.
    """

    cells = []
    for name, description in rows:
        shown = name_format.format(name)
        cells.append([f"<code>{html.escape(shown)}</code>", _reference_text(description)])

    table = _table(testid, [label, "Description"], cells)
    return table


def _events_table(rows: "list[tuple[str, str, str]]") -> str:
    """
        Render the events table, with a detail column when any event has one.

        :param rows: The (name, description, detail) triples.

        :returns: The table HTML, or "" when there are no events.
    """

    any_detail = False
    for _name, _description, detail in rows:
        if detail != "":
            any_detail = True

    cells = []
    for name, description, detail in rows:
        name_cell = f"<code>{html.escape(name)}</code>"
        if any_detail is True:
            detail_cell = f"<code>{html.escape(html.unescape(detail))}</code>" if detail != "" else ""
            cells.append([name_cell, detail_cell, _reference_text(description)])
        else:
            cells.append([name_cell, _reference_text(description)])

    if any_detail is True:
        headers = ["Event", "Detail", "Description"]
    else:
        headers = ["Event", "Description"]

    table = _table("events-table", headers, cells)
    return table


def _slots_table(rows: "list[tuple[str, str, str]]") -> str:
    """
        Render the slots table.

        :param rows: The (name, description, sample) triples.

        :returns: The table HTML, or "" when there are no slots.
    """

    cells = []
    for name, description, _sample in rows:
        if name == "":
            name_cell = '<span class="muted">(default)</span>'
        else:
            name_cell = f"<code>{html.escape(name)}</code>"
        cells.append([name_cell, _reference_text(description)])

    table = _table("slots-table", ["Slot", "Description"], cells)
    return table


def _reference_blocks(doc: ComponentDoc) -> str:
    """
        Render every non-empty reference table of a component doc.

        :param doc: The ComponentDoc.

        :returns: The labelled tables, in reading order.
    """

    blocks = [
        _optional_block(_attributes_table(doc.attributes, "attributes-table"), "Attributes"),
        _optional_block(_pairs_table(doc.properties, "Property", "properties-table"), "Properties"),
        _optional_block(_pairs_table(doc.methods, "Method", "methods-table"), "Methods"),
        _optional_block(_events_table(doc.events), "Events"),
        _optional_block(_slots_table(doc.slots), "Slots"),
        _optional_block(_pairs_table(doc.parts, "Part", "parts-table", "::part({})"), "CSS parts"),
        _optional_block(_pairs_table(doc.css_properties, "Custom property", "css-properties-table"),
                        "CSS custom properties"),
    ]

    shown = []
    for block in blocks:
        if block != "":
            shown.append(block)
    joined = "\n".join(shown)
    return joined


# ---------------------------------------------------------------------------
# Sandbox section
# ---------------------------------------------------------------------------

# Controls every chart-type page offers in addition to the type's options.
_CHART_CONTROLLER_ATTRIBUTES = [
    AttributeDoc(name="label", description="Accessible name of the chart.", kind="string"),
    AttributeDoc(name="description", description="Longer text alternative read with the chart.",
                 kind="string"),
]

_CSS_PLACEHOLDER = "/* CSS for the preview document, e.g.  mj-button { margin: 8px; } */"
_JS_PLACEHOLDER = (
    "// JavaScript, run as a module after every element is defined.\n"
    "// e.g.  document.querySelector(\"mj-button\").focus()"
)


def _attribute_payload(attributes: "list[AttributeDoc]") -> "list[dict[str, object]]":
    """
        Build the controls panel data for a list of attributes.

        :param attributes: The AttributeDoc entries.

        :returns: One dictionary per attribute, with its rendered help text.
    """

    payload = []
    for attribute in attributes:
        entry = attribute.as_dict()
        entry["descriptionHtml"] = _reference_text(attribute.description)
        payload.append(entry)

    return payload


def _gallery_chips(gallery: "list[ComponentExample]", selected: ComponentExample) -> str:
    """
        Render the example chips of the Play panel.

        :param gallery: The gallery examples.
        :param selected: The example the page opens with.

        :returns: HTML for the chip group.
    """

    chips = []
    for example in gallery:
        pressed = "true" if example.key == selected.key else "false"
        safe_key = html.escape(example.key)
        chips.append(
            f'<button type="button" class="ex-chip" data-example-chip="{safe_key}" '
            f'data-testid="example-item-{safe_key}" aria-pressed="{pressed}">'
            f'{html.escape(example.title)}</button>'
        )
    chips_html = "\n        ".join(chips)

    gallery_html = f"""<div class="gallery" role="group" aria-label="Examples" data-testid="example-gallery">
        <span class="gallery-label" aria-hidden="true">Examples</span>
        {chips_html}
      </div>"""
    return gallery_html


def _example_cards(gallery: "list[ComponentExample]", selected: ComponentExample, path: str) -> str:
    """
        Render the example cards of the Examples panel.

        :param gallery: The gallery examples.
        :param selected: The example the page opens with.
        :param path: The page path, for the deep links.

        :returns: HTML for the cards.
    """

    cards = []
    for example in gallery:
        safe_key = html.escape(example.key)
        classes = "example-card current" if example.key == selected.key else "example-card"
        link = html.escape(f"{path}?example={example.key}")
        cards.append(f"""        <article class="{classes}" data-example-card="{safe_key}" data-testid="example-card-{safe_key}">
          <div class="ex-title">{html.escape(example.title)}</div>
          <a class="ex-key" href="{link}" data-testid="example-link-{safe_key}">?example={safe_key}</a>
          <div class="ex-desc">{example.description}</div>
          <div class="ex-actions">
            <button type="button" class="btn small" data-example-view="{safe_key}"
              data-testid="example-view-{safe_key}">View here</button>
            <button type="button" class="btn small primary" data-example-open="{safe_key}"
              data-testid="example-open-{safe_key}">Open in Play</button>
          </div>
        </article>""")
    cards_html = "\n".join(cards)
    return cards_html


def _sandbox_section(
    title: str,
    mode: str,
    target: str,
    gallery: "list[ComponentExample]",
    selected: ComponentExample,
    attributes: "list[AttributeDoc]",
    slots: "list[tuple[str, str, str]]",
    presets: bool,
    path: str,
) -> str:
    """
        Render the demo section: the Examples and Play tabs with the gallery,
        the editors, the preview and the inspector, plus the page data and the
        preview bootstrap the sandbox script reads.

        :param title: The component or chart title.
        :param mode: "component", "chart" or "part".
        :param target: The tag the controls and slot inspector act on.
        :param gallery: The examples.
        :param selected: The example the page opens with.
        :param attributes: The attributes the controls panel offers.
        :param slots: The (name, description, sample) slots.
        :param presets: Whether to offer chart data presets.
        :param path: The page path, for deep links.

        :returns: HTML for the section.
    """

    safe_title = html.escape(title)
    safe_target = html.escape(target)

    slot_payload = []
    for name, description, sample in slots:
        slot_payload.append({"name": name, "description": description, "sample": sample})

    example_payload = [example.as_dict() for example in gallery]

    page_data = {
        "mode": mode,
        "target": target,
        "title": title,
        "selected": selected.key,
        "examples": example_payload,
        "attributes": _attribute_payload(attributes),
        "slots": slot_payload,
        "presets": presets,
    }
    data_json = _json_for_script(page_data)

    chips_html = _gallery_chips(gallery, selected)
    cards_html = _example_cards(gallery, selected, path)

    note_hidden = " hidden" if selected.description.strip() == "" else ""

    if len(attributes) > 0:
        controls_empty = ""
    else:
        controls_empty = '<p class="empty" data-testid="controls-empty">No attributes are documented for this page yet.</p>'

    presets_html = ""
    if presets is True:
        presets_html = """
          <div class="chart-presets" id="chart-presets" data-testid="chart-presets">
            <div class="sub-label">Sample data</div>
            <div class="preset-buttons" role="group" aria-label="Sample data presets">
              <button type="button" class="btn small" data-preset="original" data-testid="chart-preset-original" aria-pressed="true">Original</button>
              <button type="button" class="btn small" data-preset="empty" data-testid="chart-preset-empty" aria-pressed="false">Empty</button>
              <button type="button" class="btn small" data-preset="single" data-testid="chart-preset-single" aria-pressed="false">Single point</button>
              <button type="button" class="btn small" data-preset="negative" data-testid="chart-preset-negative" aria-pressed="false">Negative values</button>
              <button type="button" class="btn small" data-preset="large" data-testid="chart-preset-large" aria-pressed="false">1,000 points</button>
            </div>
            <p class="empty" id="chart-presets-note" hidden>Presets apply to data with <code>categories</code> or <code>series[].values</code>; this chart's data has neither.</p>
          </div>"""

    slot_rows = []
    for name, description, _sample in slots:
        label = "(default)" if name == "" else name
        testid_name = "default" if name == "" else name
        safe_name = html.escape(name)
        slot_rows.append(f"""            <div class="slot-row">
              <label><input type="checkbox" data-slot-toggle="{safe_name}" data-testid="slot-toggle-{html.escape(testid_name)}">
                <code>{html.escape(label)}</code></label>
              <div class="control-help">{_reference_text(description)}</div>
            </div>""")
    if len(slot_rows) > 0:
        slots_html = "\n".join(slot_rows)
    else:
        slots_html = '<p class="empty" data-testid="slots-empty">No slots are documented for this page yet.</p>'

    section = f"""
    <section class="demo" data-testid="demo-section" aria-label="{safe_title} sandbox">
      <div class="demo-bar">
        <div class="tablist" role="tablist" aria-label="{safe_title} demo" data-tabs>
          <button type="button" role="tab" id="tab-example" data-testid="tab-example"
            aria-controls="panel-example" aria-selected="false" tabindex="-1">Examples
            <span class="badge">{len(gallery)}</span></button>
          <button type="button" role="tab" id="tab-play" data-testid="tab-play"
            aria-controls="panel-play" aria-selected="true" tabindex="0">Play</button>
        </div>
      </div>

      <div role="tabpanel" id="panel-example" data-testid="panel-example"
        aria-labelledby="tab-example" hidden>
        <p class="panel-hint">Every example on this page. View one here unchanged, or open it in Play to edit it.</p>
        <div class="example-cards" data-testid="example-cards">
{cards_html}
        </div>
        <iframe class="scenario-frame" id="example-frame" data-testid="example-frame"
          title="{safe_title} example"></iframe>
      </div>

      <div role="tabpanel" id="panel-play" data-testid="panel-play" aria-labelledby="tab-play">
      {chips_html}
        <div class="example-note" id="example-description" data-testid="example-description"{note_hidden}>{selected.description}</div>

        <div class="sandbox-toolbar">
          <div class="pg-actions" data-testid="playground-controls">
            <button type="button" class="btn primary" id="pg-run" data-testid="playground-run"
              title="Run (Ctrl+Enter in an editor)">Run &#9654;</button>
            <button type="button" class="btn" id="pg-reset" data-testid="playground-reset"
              title="Restore the example">Reset</button>
            <button type="button" class="btn" id="pg-open" data-testid="playground-open"
              title="Open the preview as a full page in a new tab">Open in new tab</button>
            <button type="button" class="btn" id="pg-copy" data-testid="playground-copy"
              title="Copy the HTML, CSS and JS as one snippet"><span class="label">Copy</span></button>
          </div>
          <div class="seg" role="group" aria-label="Preview width" data-testid="preview-widths">
            <span class="seg-label" aria-hidden="true">Width</span>
            <button type="button" data-preview-width="320" data-testid="preview-width-320" aria-pressed="false">320</button>
            <button type="button" data-preview-width="768" data-testid="preview-width-768" aria-pressed="false">768</button>
            <button type="button" data-preview-width="1024" data-testid="preview-width-1024" aria-pressed="false">1024</button>
            <button type="button" data-preview-width="full" data-testid="preview-width-full" aria-pressed="true">Full</button>
          </div>
          <div class="seg" role="group" aria-label="Preview theme" data-testid="preview-themes">
            <span class="seg-label" aria-hidden="true">Theme</span>
            <button type="button" data-preview-theme="light" data-testid="preview-theme-light" aria-pressed="true">Light</button>
            <button type="button" data-preview-theme="dark" data-testid="preview-theme-dark" aria-pressed="false">Dark</button>
            <button type="button" data-preview-theme="os" data-testid="preview-theme-os" aria-pressed="false">OS</button>
          </div>
          <div class="seg" role="group" aria-label="Text direction" data-testid="preview-dirs">
            <span class="seg-label" aria-hidden="true">Dir</span>
            <button type="button" data-preview-dir="ltr" data-testid="preview-dir-ltr" aria-pressed="true">LTR</button>
            <button type="button" data-preview-dir="rtl" data-testid="preview-dir-rtl" aria-pressed="false">RTL</button>
          </div>
          <span class="size-readout" id="preview-size" data-testid="preview-size"></span>
          <span class="visually-hidden" id="sandbox-status" role="status"></span>
        </div>

        <div class="sandbox-stage">
          <div class="preview-area">
            <div class="preview-stage" id="preview-stage" data-testid="preview-stage">
              <div class="preview-box" id="preview-box">
                <iframe class="pg-preview" id="pg-frame" data-testid="playground-preview"
                  title="Live {safe_title} preview"></iframe>
                <div class="resize-handle" id="preview-resize-handle" data-testid="preview-resize-handle"
                  role="separator" aria-orientation="vertical" tabindex="0"
                  aria-label="Drag to resize the preview width (arrow keys also work)"></div>
              </div>
            </div>
          </div>

          <aside class="inspector" data-testid="inspector" aria-label="Inspector">
            <div class="tablist" role="tablist" aria-label="Inspector" data-tabs>
              <button type="button" role="tab" id="tab-controls" data-testid="inspector-tab-controls"
                aria-controls="panel-controls" aria-selected="true" tabindex="0">Controls</button>
              <button type="button" role="tab" id="tab-slots" data-testid="inspector-tab-slots"
                aria-controls="panel-slots" aria-selected="false" tabindex="-1">Slots</button>
              <button type="button" role="tab" id="tab-events" data-testid="inspector-tab-events"
                aria-controls="panel-events" aria-selected="false" tabindex="-1">Events
                <span class="badge" data-event-count>0</span></button>
              <button type="button" role="tab" id="tab-errors" data-testid="inspector-tab-errors"
                aria-controls="panel-errors" aria-selected="false" tabindex="-1">Errors
                <span class="badge" data-error-count>0</span></button>
            </div>
            <div role="tabpanel" id="panel-controls" data-testid="controls-panel" aria-labelledby="tab-controls">
{presets_html}
              <p class="panel-hint">Changes apply live to the first <code>&lt;{safe_target}&gt;</code> in the preview and update the HTML pane.</p>
              <p class="empty" id="controls-missing" data-testid="controls-missing" hidden>There is no <code>&lt;{safe_target}&gt;</code> in the preview.</p>
              {controls_empty}
              <div id="controls-list" data-testid="controls-list"></div>
            </div>
            <div role="tabpanel" id="panel-slots" data-testid="slot-inspector" aria-labelledby="tab-slots" hidden>
              <p class="panel-hint">Switch slot content of the first <code>&lt;{safe_target}&gt;</code> off and on.</p>
{slots_html}
            </div>
            <div role="tabpanel" id="panel-events" data-testid="event-log-panel" aria-labelledby="tab-events" hidden>
              <div class="panel-toolbar">
                <span id="event-log-count" data-testid="event-log-count">0 events</span>
                <input type="search" id="event-log-filter" data-testid="event-log-filter"
                  placeholder="Filter" aria-label="Filter events">
                <button type="button" class="btn small" id="event-log-clear" data-testid="event-log-clear">Clear</button>
              </div>
              <ol class="log" id="event-log" data-testid="event-log" reversed></ol>
            </div>
            <div role="tabpanel" id="panel-errors" data-testid="error-panel" aria-labelledby="tab-errors" hidden>
              <div class="panel-toolbar">
                <span id="error-count" class="grow" data-testid="error-count">0 errors</span>
                <button type="button" class="btn small" id="error-clear" data-testid="error-clear">Clear</button>
              </div>
              <p class="empty" id="error-empty">No uncaught errors or unhandled rejections in the preview.</p>
              <ol class="error-list" id="error-list" data-testid="error-list"></ol>
            </div>
          </aside>

          <div class="pg-code">
            <div class="pg-pane">
              <label for="pg-code">HTML</label>
              <textarea id="pg-code" data-testid="playground-editor"
                spellcheck="false">{html.escape(selected.html)}</textarea>
            </div>
            <div class="pg-pane">
              <label for="pg-style">CSS</label>
              <textarea id="pg-style" data-testid="playground-style-editor" spellcheck="false"
                placeholder="{html.escape(_CSS_PLACEHOLDER)}">{html.escape(selected.css)}</textarea>
            </div>
            <div class="pg-pane">
              <label for="pg-script">JS</label>
              <textarea id="pg-script" data-testid="playground-script-editor" spellcheck="false"
                placeholder="{html.escape(_JS_PLACEHOLDER)}">{html.escape(selected.script)}</textarea>
            </div>
          </div>
        </div>
      </div>
      <script type="application/json" id="sandbox-data">{data_json}</script>
      <script type="text/x-mj-preview-boot" id="sandbox-preview-boot">{_PREVIEW_BOOT_JS}</script>
    </section>"""
    return section


def _pager(
    previous_link: "tuple[str, str] | None",
    next_link: "tuple[str, str] | None",
    label: str,
    position: str,
    bottom: bool = False,
) -> str:
    """
        Render previous / next links of a detail page.

        :param previous_link: (href, title) of the previous page, or None.
        :param next_link: (href, title) of the next page, or None.
        :param label: The accessible name of the navigation.
        :param position: e.g. "3 of 18", shown between the links.
        :param bottom: True for the copy at the bottom of the page.

        :returns: HTML for the navigation.
    """

    suffix = "-bottom" if bottom is True else ""
    links = []
    if previous_link is not None:
        href, title = previous_link
        links.append(
            f'<a href="{html.escape(href)}" rel="prev" data-testid="page-prev{suffix}">'
            f'&larr; {html.escape(title)}</a>'
        )
    if position != "":
        links.append(f'<span class="pager-pos">{html.escape(position)}</span>')
    if next_link is not None:
        href, title = next_link
        links.append(
            f'<a href="{html.escape(href)}" rel="next" data-testid="page-next{suffix}">'
            f'{html.escape(title)} &rarr;</a>'
        )

    classes = "pager bottom" if bottom is True else "pager"
    links_html = "\n      ".join(links)
    pager = f"""<nav class="{classes}" aria-label="{html.escape(label)}" data-testid="pager{suffix}">
      {links_html}
    </nav>"""
    return pager


# ---------------------------------------------------------------------------
# Detail pages
# ---------------------------------------------------------------------------

def render_component_page(group_key: str, tag: str, example_key: "str | None" = None) -> "str | None":
    """
        Render the sandbox page for one component.

        Page layout (top to bottom):
          1. Heading with previous / next links, and the one-line summary,
             so the sandbox starts within the first screen.
          2. The demo section -- the Play tab (gallery, editors, preview,
             inspector) selected, and the Examples tab.
          3. The full description (never clipped), how-to guidance, then the
             reference tables that have rows.

        :param group_key: The owning group key.
        :param tag: The component tag.
        :param example_key: The ``?example=`` key to open with, or None.

        :returns: The HTML document, or None if the component is unknown.
    """

    doc = component_for(group_key, tag)
    if doc is None:
        return None

    group = group_by_key(group_key)
    safe_group_title = html.escape(group.title)
    safe_tag = html.escape(doc.tag)
    safe_title = html.escape(doc.title)
    path = f"/components/{group_key}/{doc.tag}"

    selected = doc.example_for(example_key)

    siblings = group_components(group_key)
    position_index = 0
    for index, sibling in enumerate(siblings):
        if sibling.tag == doc.tag:
            position_index = index + 1
    previous_doc, next_doc = component_neighbours(group_key, doc.tag)
    previous_link = None
    next_link = None
    if previous_doc is not None:
        previous_link = (f"/components/{group_key}/{previous_doc.tag}", previous_doc.title)
    if next_doc is not None:
        next_link = (f"/components/{group_key}/{next_doc.tag}", next_doc.title)
    position = f"{position_index} of {len(siblings)} in {group.title}"
    pager_label = f"Components in {group.title}"

    sandbox = _sandbox_section(
        title=doc.title,
        mode="component",
        target=doc.tag,
        gallery=doc.gallery,
        selected=selected,
        attributes=doc.attributes,
        slots=doc.slots,
        presets=False,
        path=path,
    )

    body = f"""
    <div class="crumbs"><a href="/">Home</a> /
      <a href="/components/{group_key}">{safe_group_title}</a> / {safe_tag}</div>
    <div class="detail-head">
      <h1 data-testid="component-heading">{safe_title}
        <span class="count">&lt;{safe_tag}&gt;</span></h1>
      {_pager(previous_link, next_link, pager_label, position)}
    </div>

    <p class="lead summary" data-testid="component-summary">{doc.summary}</p>
{sandbox}

    <div class="section-label">About</div>
    <div class="doc-body description" data-testid="component-description">{doc.description}</div>

    <div class="section-label">How to use it</div>
    <div class="doc-body" data-testid="component-howto">{doc.how_to_use}</div>

    {_reference_blocks(doc)}

    {_pager(previous_link, next_link, pager_label, position, bottom=True)}"""

    document = page_shell(
        title=doc.title,
        body_html=body,
        extra_js=_SANDBOX_JS,
        active_view=_view_for(group_key, tag),
        main_class="detail",
    )
    return document


def render_chart_type_page(type_key: str, example_key: "str | None" = None) -> "str | None":
    """
        Render the sandbox page for one <mj-chart> chart type.

        :param type_key: The chart type key.
        :param example_key: The ``?example=`` key to open with, or None.

        :returns: The complete HTML document, or None if unknown.
    """

    from testcomponents.charttypes import CHART_CATEGORIES
    from testcomponents.charttypes import chart_type_for
    from testcomponents.charttypes import chart_type_neighbours

    doc = chart_type_for(type_key)
    if doc is None:
        return None

    safe_type = html.escape(doc.type_key)
    safe_title = html.escape(doc.title)
    # Summary and description are plain text: entities decoded, escaped,
    # `backticks` as code (contract section 6).
    safe_summary = _reference_text(doc.summary)
    path = f"/chart-type/{doc.type_key}"

    category_title = doc.category
    for key, title, _accent in CHART_CATEGORIES:
        if key == doc.category:
            category_title = title
    safe_category = html.escape(category_title)

    selected = doc.example_for(example_key)

    attributes = list(doc.options)
    documented = set()
    for option in doc.options:
        documented.add(option.name)
    for generic in _CHART_CONTROLLER_ATTRIBUTES:
        if generic.name not in documented:
            attributes.append(generic)

    previous_doc, next_doc = chart_type_neighbours(doc.type_key)
    previous_link = None
    next_link = None
    if previous_doc is not None:
        previous_link = (f"/chart-type/{previous_doc.type_key}", previous_doc.title)
    if next_doc is not None:
        next_link = (f"/chart-type/{next_doc.type_key}", next_doc.title)

    sandbox = _sandbox_section(
        title=doc.title,
        mode="chart",
        target="mj-chart",
        gallery=doc.gallery,
        selected=selected,
        attributes=attributes,
        slots=[],
        presets=True,
        path=path,
    )

    description_html = ""
    if doc.description.strip() != "":
        description_html = f"""
    <div class="section-label">About</div>
    <div class="doc-body description" data-testid="chart-type-description">{_plain_paragraphs(doc.description)}</div>"""

    data_shape_html = ""
    if doc.data_shape.strip() != "":
        data_shape_html = f"""
    <div class="section-label">Data shape</div>
    <div class="doc-body data-shape" data-testid="chart-type-data-shape">{doc.data_shape}</div>"""

    options_html = _optional_block(_attributes_table(doc.options, "options-table"), "Options")
    events_html = _optional_block(_events_table(doc.events), "Events")

    body = f"""
    <div class="crumbs"><a href="/charts">Charts</a> /
      <a href="/charts#chart-category-{html.escape(doc.category)}">{safe_category}</a> / {safe_title}</div>
    <div class="detail-head">
      <h1 data-testid="chart-type-heading">{safe_title}
        <span class="count">type="{safe_type}"</span></h1>
      {_pager(previous_link, next_link, "Chart types", "")}
    </div>

    <p class="lead summary" data-testid="chart-type-summary">{safe_summary}</p>
{sandbox}
{description_html}
{data_shape_html}
    {options_html}
    {events_html}

    <div class="section-label">Category</div>
    <div class="doc-body" data-testid="chart-type-category">{safe_category}</div>

    {_pager(previous_link, next_link, "Chart types", "", bottom=True)}"""

    document = page_shell(
        title=doc.title,
        body_html=body,
        extra_js=_SANDBOX_JS,
        active_view="charts",
        main_class="detail",
    )
    return document


def render_chart_part_page(tag: str, example_key: "str | None" = None) -> "str | None":
    """
        Render the sandbox page for one chart part component.

        :param tag: The part tag, e.g. ``mj-chart-legend``.
        :param example_key: The ``?example=`` key to open with, or None.

        :returns: The complete HTML document, or None if unknown.
    """

    from testcomponents.charttypes import CHART_PARTS
    from testcomponents.charttypes import chart_part_for

    doc = chart_part_for(tag)
    if doc is None:
        return None

    safe_tag = html.escape(doc.tag)
    safe_title = html.escape(doc.title)
    path = f"/chart-part/{doc.tag}"
    selected = doc.example_for(example_key)

    previous_link = None
    next_link = None
    position = ""
    for index, part in enumerate(CHART_PARTS):
        if part.tag == doc.tag:
            position = f"{index + 1} of {len(CHART_PARTS)} chart parts"
            if index > 0:
                before = CHART_PARTS[index - 1]
                previous_link = (f"/chart-part/{before.tag}", before.title)
            if index + 1 < len(CHART_PARTS):
                after = CHART_PARTS[index + 1]
                next_link = (f"/chart-part/{after.tag}", after.title)

    sandbox = _sandbox_section(
        title=doc.title,
        mode="part",
        target=doc.tag,
        gallery=doc.gallery,
        selected=selected,
        attributes=doc.attributes,
        slots=doc.slots,
        presets=True,
        path=path,
    )

    body = f"""
    <div class="crumbs"><a href="/charts">Charts</a> /
      <a href="/charts#charts-section-parts">Chart parts</a> / {safe_tag}</div>
    <div class="detail-head">
      <h1 data-testid="component-heading">{safe_title}
        <span class="count">&lt;{safe_tag}&gt;</span></h1>
      {_pager(previous_link, next_link, "Chart parts", position)}
    </div>

    <p class="lead summary" data-testid="component-summary">{doc.summary}</p>
{sandbox}

    <div class="section-label">About</div>
    <div class="doc-body description" data-testid="component-description">{doc.description}</div>

    <div class="section-label">How to use it</div>
    <div class="doc-body" data-testid="component-howto">{doc.how_to_use}</div>

    {_reference_blocks(doc)}

    {_pager(previous_link, next_link, "Chart parts", position, bottom=True)}"""

    document = page_shell(
        title=doc.title,
        body_html=body,
        extra_js=_SANDBOX_JS,
        active_view="charts",
        main_class="detail",
    )
    return document
