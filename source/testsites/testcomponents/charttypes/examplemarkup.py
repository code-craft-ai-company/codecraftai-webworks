"""
    examplemarkup.py

    Shared builders for the chart-type catalog modules (``_01`` .. ``_06``):
    the JSON writers that put example data into an example's markup, the
    ``<mj-chart>`` markup and gallery-example builders, the events-example
    builder, and the option docs that several chart families share
    (boolean options, true / false options decided by the data, orientation).

    Example data is kept as Python dictionaries and written into each
    example's markup as inline JSON (``<script type="application/json">``),
    so the chart-type page's data presets can read it.
"""

import copy
import json

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentExample


# ---------------------------------------------------------------------------
# JSON writers
# ---------------------------------------------------------------------------

#: Line width the multi-line JSON of the examples is wrapped at.
JSON_WIDTH = 92


def _json_one_line(value: object) -> str:
    """
        Write a JSON value on one line with readable separators.

        :param value: A JSON-serialisable value.

        :returns: The JSON text.
    """

    text = json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    return text


def json_text(value: object, indent: int = 2) -> str:
    """
        Write a JSON value for an example's HTML pane: a container that fits
        on one line stays on one line, a longer one is broken into one member
        per line (numbers and strings of a long list are packed several to a
        line).

        :param value: A JSON-serialisable value.
        :param indent: The column the value starts at (used for the width test
            and the indentation of nested lines).

        :returns: The JSON text (``</`` is written as ``<\\/`` so the text can
            sit inside a ``<script>`` element).
    """

    text = _json_one_line(value)
    is_container = isinstance(value, (dict, list)) and len(value) > 0
    if is_container is False or len(text) + indent <= JSON_WIDTH:
        return text.replace("</", "<\\/")

    pad = " " * (indent + 2)
    closing = " " * indent
    if isinstance(value, dict):
        members = []
        for key, member in value.items():
            members.append(pad + _json_one_line(key) + ": " + json_text(member, indent + 2))
        text = "{\n" + ",\n".join(members) + "\n" + closing + "}"
        return text

    scalars = all(isinstance(member, (dict, list)) is False for member in value)
    if scalars is True:
        lines = []
        current = ""
        for member in value:
            piece = _json_one_line(member)
            if current != "" and len(pad) + len(current) + len(piece) + 2 > JSON_WIDTH:
                lines.append(pad + current + ",")
                current = piece
            elif current == "":
                current = piece
            else:
                current = current + ", " + piece
        lines.append(pad + current)
        text = "[\n" + "\n".join(lines) + "\n" + closing + "]"
        return text.replace("</", "<\\/")

    members = [pad + json_text(member, indent + 2) for member in value]
    text = "[\n" + ",\n".join(members) + "\n" + closing + "]"
    return text


def compact_json(value: object) -> str:
    """
        Write a JSON value compactly on one line (no spaces after separators).

        :param value: A JSON-serialisable value.

        :returns: The JSON text (``</`` is written as ``<\\/`` so the text can
            sit inside a ``<script>`` element).
    """

    text = json.dumps(value, separators=(",", ":"))
    return text.replace("</", "<\\/")


def inline_json_script(value: object) -> str:
    """
        An inline ``<script type="application/json">`` element holding a value
        as compact JSON.

        :param value: A JSON-serialisable value.

        :returns: The HTML text.
    """

    markup = f'<script type="application/json">{compact_json(value)}</script>'
    return markup


# ---------------------------------------------------------------------------
# Chart markup and gallery examples
# ---------------------------------------------------------------------------

def chart_markup(type_key: str, data: object, attributes: "dict[str, str] | None" = None,
                 height: int = 260, legend: bool = False, chart_id: "str | None" = None) -> str:
    """
        Build the markup of one <mj-chart> with inline JSON data.

        :param type_key: The chart type.
        :param data: The chart data (JSON-serialisable).
        :param attributes: Extra host attributes in markup order, e.g.
            ``{"variant": "filled"}``. A value of ``""`` writes a bare
            attribute (``<mj-chart notched>``).
        :param height: The chart height in px (inline style).
        :param legend: Whether to nest an <mj-chart-legend>.
        :param chart_id: Optional element id.

        :returns: The HTML text.
    """

    parts = []
    if chart_id is not None:
        parts.append(f'id="{chart_id}"')
    parts.append(f'type="{type_key}"')
    if attributes is not None:
        for name, value in attributes.items():
            if value == "":
                parts.append(name)
            else:
                parts.append(f'{name}="{value}"')
    parts.append(f'style="height:{height}px"')

    lines = ["<mj-chart " + " ".join(parts) + ">"]
    if legend is True:
        lines.append("  <mj-chart-legend></mj-chart-legend>")
    lines.append('  <script type="application/json">')
    lines.append("  " + json_text(data, 2))
    lines.append("  </script>")
    lines.append("</mj-chart>")
    markup = "\n".join(lines)
    return markup


def gallery_example(key: str, title: str, description: str, html: str, script: str = "",
                    css: str = "") -> ComponentExample:
    """
        Build one gallery entry.

        :param key: The example key.
        :param title: The gallery chip title.
        :param description: HTML: what to look at / try.
        :param html: The preview markup.
        :param script: Optional module script.
        :param css: Optional CSS.

        :returns: The ComponentExample.
    """

    example = ComponentExample(key=key, title=title, description=description, html=html,
                               script=script, css=css)
    return example


def basic_example(html: str, description: str) -> ComponentExample:
    """
        The first gallery entry: the canonical example of the type.

        :param html: The markup.
        :param description: What to look at (HTML).

        :returns: A ComponentExample keyed ``basic``.
    """

    example = gallery_example("basic", "Basic usage", description, html)
    return example


def chart_example(key: str, title: str, description: str, type_key: str, data: object,
                  attributes: "dict[str, str] | None" = None, height: int = 260,
                  legend: bool = False) -> ComponentExample:
    """
        Build a gallery example holding one chart.

        :param key: The example key.
        :param title: The gallery chip title.
        :param description: HTML: what to look at / try.
        :param type_key: The chart type.
        :param data: The chart data.
        :param attributes: Extra host attributes.
        :param height: The chart height in px.
        :param legend: Whether to nest an <mj-chart-legend>.

        :returns: The ComponentExample.
    """

    example = gallery_example(key, title, description,
                              chart_markup(type_key, data, attributes, height, legend))
    return example


# The events example's styles: the detail read-out under the chart.
EVENTS_CSS = (
    ".event-detail {\n"
    "  display: block;\n"
    "  margin-block-start: var(--mj-space-2);\n"
    "  font-family: var(--mj-font-mono);\n"
    "  font-size: var(--mj-font-size-sm);\n"
    "  color: var(--mj-text-muted);\n"
    "  overflow-wrap: anywhere;\n"
    "}\n"
)


def events_script(event_names: "list[str]", activate: bool = True) -> str:
    """
        Build the script of an events example: listen for the renderer's
        events, show the last detail under the chart, and (optionally) click
        the first focusable mark once the chart is drawn so the Events panel
        shows the event straight away.

        :param event_names: The events to listen for.
        :param activate: Whether to click the first mark after the first draw.

        :returns: The module script text.
    """

    names = ", ".join(json.dumps(name) for name in event_names)
    lines = [
        'const chart = document.getElementById("events-chart")',
        'const output = document.getElementById("events-detail")',
        "",
        f"for (const name of [{names}]) {{",
        "  chart.addEventListener(name, (event) => {",
        '    output.textContent = name + " " + JSON.stringify(event.detail)',
        "  })",
        "}",
    ]
    if activate is True:
        lines.extend([
            "",
            "// Wait for the first draw, then click the first mark as a user would.",
            'if (chart.chartState !== "ready") {',
            "  await new Promise((resolve) => {",
            '    chart.addEventListener("mj-chart-render", resolve, { once: true })',
            "    setTimeout(resolve, 3000)",
            "  })",
            "}",
            'const mark = chart.shadowRoot.querySelector("svg [tabindex]")',
            "if (mark !== null) {",
            "  const box = mark.getBoundingClientRect()",
            '  mark.dispatchEvent(new MouseEvent("click", {',
            "    bubbles: true, clientX: box.left + box.width / 2, clientY: box.top + box.height / 2",
            "  }))",
            '  mjSandbox.log("clicked the first mark", { part: mark.getAttribute("part") })',
            "}",
        ])
    script = "\n".join(lines) + "\n"
    return script


def events_example(type_key: str, data: object, event_names: "list[str]", description: str,
                   attributes: "dict[str, str] | None" = None, height: int = 260,
                   legend: bool = False, title: str = "Events") -> ComponentExample:
    """
        Build the events example of a chart type: the chart (id
        ``events-chart``), a read-out of the last event detail and a script
        that listens for the renderer's events and clicks the first mark.

        :param type_key: The chart type.
        :param data: The chart data.
        :param event_names: The renderer events the script listens for.
        :param description: HTML: which marks emit what.
        :param attributes: Extra host attributes.
        :param height: The chart height in px.
        :param legend: Whether to nest an <mj-chart-legend>.
        :param title: The gallery chip title.

        :returns: The ComponentExample.
    """

    markup = chart_markup(type_key, data, attributes, height, legend, chart_id="events-chart")
    html = (
        markup + "\n"
        '<output id="events-detail" class="event-detail" for="events-chart">'
        "Click a mark, or focus the chart and press Enter.</output>"
    )
    example = ComponentExample(
        key="events",
        title=title,
        description=description,
        html=html,
        css=EVENTS_CSS,
        script=events_script(event_names),
    )
    return example


def with_changes(data: dict, **changes: object) -> dict:
    """
        Copy example data and replace some of its top-level members.

        :param data: The data to copy (left unchanged).
        :param changes: Top-level members to set; a value of None removes the
            member.

        :returns: The new data dictionary.
    """

    result = copy.deepcopy(data)
    for name, value in changes.items():
        if value is None:
            result.pop(name, None)
        else:
            result[name] = value
    return result


# ---------------------------------------------------------------------------
# Shared option docs
# ---------------------------------------------------------------------------

def boolean_option(name: str, description: str, default: bool = False) -> AttributeDoc:
    """
        Document a boolean renderer option. Every renderer reads boolean
        options the same way (charts/core/chartoptions.js): a present
        attribute is on (``<mj-chart notched>``, ``notched=""``,
        ``notched="true"``) unless its value is ``"false"``.

        :param name: The attribute name.
        :param description: What it does.
        :param default: True for an option that is on when the attribute is
            absent (switched off with ``name="false"``).

        :returns: The AttributeDoc (kind ``boolean``).
    """

    option = AttributeDoc(name=name, description=description, kind="boolean",
                          default="true" if default is True else "false")
    return option


def true_false_option(name: str, description: str, default: "str | None") -> AttributeDoc:
    """
        Document a boolean option whose absence leaves the decision to the
        data (``fill`` of a polar chart reads ``data.fill`` when the attribute
        is absent): an enum, so "(not set)" stays distinct from ``false``. A
        bare attribute reads as ``true`` like any boolean option.

        :param name: The attribute name.
        :param description: What it does.
        :param default: The behaviour when absent ("true", "false" or None
            when the data decides).

        :returns: The AttributeDoc.
    """

    option = AttributeDoc(name=name, description=description, kind="enum",
                          values=["true", "false"], default=default)
    return option


def orientation_option(default: "str | None", description: "str | None" = None) -> AttributeDoc:
    """
        The ``orientation`` option.

        :param default: The registered default, or None when the renderer picks.
        :param description: The option's description (default: "Direction of
            the layout.").

        :returns: An AttributeDoc.
    """

    text = description if description is not None and description != "" else "Direction of the layout."
    option = AttributeDoc(name="orientation", description=text, kind="enum",
                          values=["vertical", "horizontal"], default=default)
    return option
