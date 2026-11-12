"""
.. module:: test_staticassets
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Static guardrail checks over the shipped web component assets.

.. moduleauthor:: Code Craft AI LLC

The mj-* component library and the chart library are served from ``ccai/webworks/static`` without a
build step, so nothing compiles or lints them before they ship. These tests read the shipped files
and enforce three rules:

1. Every ``var(--mj-*)`` written without a fallback names a design token that ``styles/tokens.css``
   defines, or a custom property the same file declares itself (a component-local property set on
   ``:host``). An undefined custom property without a fallback silently computes to the property's
   initial value, so the declaration does nothing and theming breaks.
2. ``styles/base.css`` and the ``BASE_CSS`` string in ``javascript/core/basestyles.js`` hold the same
   rules once comments and whitespace are stripped. Components adopt the JavaScript copy; the CSS
   file documents it; the two must be changed together.
3. No ``innerHTML`` assignment and no ``insertAdjacentHTML`` call takes a template literal with
   ``${...}`` interpolation that is not tagged with ``html`` from ``core/html.js``. The ``html`` tag
   escapes every interpolated value; an untagged template inserts it as live markup.

Rule 3 reads the JavaScript with a small lexer (strings, comments, regular expression literals and
nested template literals) and inspects the expression on the right of each markup sink. It does not
follow values through variables or function calls: ``el.innerHTML = this._markup()`` is checked where
``_markup`` builds its string, not here.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import difflib
import os
import re

from typing import Any, Dict, List, Set, Tuple

import ccai.testbase as testbase

import ccai.webworks


# =============================================================================
# Locations
# =============================================================================

STATIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(ccai.webworks.__file__)), "static")
JAVASCRIPT_ROOT = os.path.join(STATIC_ROOT, "javascript")
STYLES_ROOT = os.path.join(STATIC_ROOT, "styles")
TOKENS_CSS_PATH = os.path.join(STYLES_ROOT, "tokens.css")
BASE_CSS_PATH = os.path.join(STYLES_ROOT, "base.css")
BASESTYLES_JS_PATH = os.path.join(JAVASCRIPT_ROOT, "core", "basestyles.js")


# =============================================================================
# Patterns
# =============================================================================

CSS_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)

# A custom property declaration: `--mj-name:` (in tokens.css, a component's :host rule ...).
DECLARATION_PATTERN = re.compile(r"(--mj-[A-Za-z0-9_-]+)\s*:")

# A custom property set from script: `style.setProperty("--mj-name", ...)`.
SET_PROPERTY_PATTERN = re.compile(r"setProperty\(\s*[\"'](--mj-[A-Za-z0-9_-]+)[\"']")

# A `var()` reference to an --mj-* property; group 2 is "," when a fallback follows, ")" otherwise.
# Names built at run time (`var(--mj-chart-series-${index})`) do not match and are not checked.
VAR_REFERENCE_PATTERN = re.compile(r"var\(\s*(--mj-[A-Za-z0-9_-]+)\s*([,)])")

BASE_CSS_STRING_PATTERN = re.compile(r"const BASE_CSS = `(.*?)`;", re.DOTALL)

INNER_HTML_SINK_PATTERN = re.compile(r"\.innerHTML\s*\+?=(?!=)")
INSERT_ADJACENT_HTML_SINK_PATTERN = re.compile(r"\.insertAdjacentHTML\s*\(")

IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9_$]+")

# The identifier directly before a backtick (spaces and tabs allowed) is the template's tag.
TEMPLATE_TAG_PATTERN = re.compile(r"([A-Za-z_$][A-Za-z0-9_$]*)[ \t]*$")

# Words after which an expression starts: a backtick after them is an untagged template and a
# slash starts a regular expression literal.
KEYWORDS_BEFORE_EXPRESSION = frozenset([
    "return", "typeof", "case", "else", "in", "of", "yield", "await", "void", "delete", "throw",
    "new", "instanceof", "do",
])

# Characters after which a slash starts a regular expression literal rather than a division.
REGEX_PRECEDERS = frozenset("(,=:[!&|?{};+-*%<>~^")

# A line break does not end an expression after these characters, nor before a line starting with
# the characters of EXPRESSION_CONTINUES_BEFORE (the code base omits statement semicolons).
EXPRESSION_CONTINUES_AFTER = frozenset("+-*/%=&|?:,.([{<>!~^")
EXPRESSION_CONTINUES_BEFORE = frozenset(".?:+-*/%&|,=")

# Marker for "the previous significant code was an operand" (identifier, number, literal).
OPERAND = "a"

# The scan of the shipped library must see at least this many markup sinks and var() references;
# fewer means the scanner, not the code, went wrong.
MINIMUM_EXPECTED_SINKS = 50
MINIMUM_EXPECTED_VAR_REFERENCES = 1000


# =============================================================================
# File helpers
# =============================================================================

def _list_files(root: str, extensions: Tuple[str, ...]) -> List[str]:
    """
        List the files below a directory whose names end with one of the extensions.

        :param root: The directory to walk.
        :param extensions: The file name endings to keep, e.g. (".js",).

        :returns: The absolute paths, sorted.
    """
    found = []
    for directory, _subdirectories, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(extensions) is True:
                found.append(os.path.join(directory, filename))
    found.sort()
    return found


def _read_text(path: str) -> str:
    """
        Read a UTF-8 text file.

        :param path: The file to read.

        :returns: The file content.
    """
    with open(path, "r", encoding="utf-8") as stream:
        content = stream.read()
    return content


def _relative_name(path: str) -> str:
    """
        The path of a static asset relative to the static root, for messages.

        :param path: An absolute path below STATIC_ROOT.

        :returns: e.g. "javascript/components/mjlightbox.js".
    """
    relative = os.path.relpath(path, STATIC_ROOT).replace(os.sep, "/")
    return relative


def _line_of(text: str, offset: int) -> int:
    """
        The 1-based line number of a character offset.

        :param text: The text the offset points into.
        :param offset: The character offset.

        :returns: The line number.
    """
    line = text.count("\n", 0, offset) + 1
    return line


def _blank_span(characters: List[str], start: int, end: int) -> None:
    """
        Replace the characters of a span with spaces, keeping line breaks so offsets and line numbers
        stay valid.

        :param characters: The text as a mutable list of characters.
        :param start: First offset of the span.
        :param end: Offset after the span.
    """
    for index in range(start, end):
        if characters[index] != "\n":
            characters[index] = " "
    return


def _blank_css_comments(text: str) -> str:
    """
        Blank out the /* ... */ comments of CSS text, keeping offsets.

        :param text: CSS text.

        :returns: The text without comments.
    """
    characters = list(text)
    for match in CSS_COMMENT_PATTERN.finditer(text):
        _blank_span(characters, match.start(), match.end())
    blanked = "".join(characters)
    return blanked


# =============================================================================
# JavaScript lexer
# =============================================================================

def _skip_quoted_string(text: str, start: int) -> int:
    """
        Find the end of a single- or double-quoted string literal.

        :param text: The JavaScript source.
        :param start: Offset of the opening quote.

        :returns: The offset after the closing quote (or after the line, for an unterminated string).
    """
    quote = text[start]
    index = start + 1
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == quote or char == "\n":
            break
        index += 1
    end = min(index + 1, length)
    return end


def _skip_regex_literal(text: str, start: int) -> int:
    """
        Find the end of a regular expression literal, including its flags.

        :param text: The JavaScript source.
        :param start: Offset of the opening slash.

        :returns: The offset after the last flag character.
    """
    index = start + 1
    length = len(text)
    in_class = False
    while index < length:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "\n":
            break
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "/" and in_class is False:
            break
        index += 1
    index += 1
    while index < length and text[index].isalpha() is True:
        index += 1
    end = min(index, length)
    return end


def _template_tag(text: str, backtick: int) -> str:
    """
        The tag of the template literal that starts at a backtick.

        :param text: The JavaScript source.
        :param backtick: Offset of the opening backtick.

        :returns: The tag identifier (e.g. "html"), or "" for an untagged template.
    """
    tag = ""
    match = TEMPLATE_TAG_PATTERN.search(text, max(0, backtick - 64), backtick)
    if match is not None:
        word = match.group(1)
        if word not in KEYWORDS_BEFORE_EXPRESSION and word[0].isdigit() is False:
            tag = word
    return tag


def _scan_javascript(text: str) -> Dict[str, Any]:
    """
        Lex JavaScript source just far enough to know where its comments, string, regular expression
        and template literals are.

        :param text: The JavaScript source.

        :returns: A dictionary with
            ``templates``: one record per template literal, in source order: ``start`` (offset of the
            opening backtick), ``end`` (offset after the closing one), ``tag`` ("" when untagged),
            ``interpolated`` (has ``${...}``), ``parent`` (index of the template whose interpolation
            holds it, -1 at the top level) and ``line``;
            ``skips``: offset of the first character of each comment and literal -> offset after it;
            ``comment_starts``: the set of offsets in ``skips`` that start a comment;
            ``code``: the text with comments, string and regex literals and the literal text of
            templates blanked out (template interpolations are kept, they are code).
    """
    templates = []
    skips = {}
    comment_starts = set()
    code = list(text)

    # Each frame is a lexer mode: "code" (top level or inside a ${...}) or "template" (literal text).
    # `depth` counts open braces in a code frame so the "}" that closes a ${...} can be told apart.
    stack = [{"mode": "code", "depth": 0, "template": -1}]
    previous = ""
    previous_word = ""
    index = 0
    length = len(text)

    while index < length:
        frame = stack[-1]
        char = text[index]

        if frame["mode"] == "template":
            record = templates[frame["template"]]
            if char == "\\":
                _blank_span(code, index, min(index + 2, length))
                index += 2
            elif char == "`":
                record["end"] = index + 1
                skips[record["start"]] = record["end"]
                stack.pop()
                previous = OPERAND
                previous_word = ""
                index += 1
            elif char == "$" and text.startswith("{", index + 1) is True:
                record["interpolated"] = True
                stack.append({"mode": "code", "depth": 0, "template": frame["template"]})
                previous = "{"
                previous_word = ""
                index += 2
            else:
                _blank_span(code, index, index + 1)
                index += 1
            continue

        if text.startswith("//", index) is True:
            end = text.find("\n", index)
            if end < 0:
                end = length
            skips[index] = end
            comment_starts.add(index)
            _blank_span(code, index, end)
            index = end
            continue

        if text.startswith("/*", index) is True:
            end = text.find("*/", index + 2)
            if end < 0:
                end = length
            else:
                end = end + 2
            skips[index] = end
            comment_starts.add(index)
            _blank_span(code, index, end)
            index = end
            continue

        if char == "'" or char == "\"":
            end = _skip_quoted_string(text, index)
            skips[index] = end
            _blank_span(code, index, end)
            previous = OPERAND
            previous_word = ""
            index = end
            continue

        if char == "`":
            record = {
                "start": index,
                "end": None,
                "tag": _template_tag(text, index),
                "interpolated": False,
                "parent": frame["template"],
                "line": _line_of(text, index),
            }
            templates.append(record)
            stack.append({"mode": "template", "depth": 0, "template": len(templates) - 1})
            index += 1
            continue

        if char == "/":
            starts_regex = False
            if previous == "" or previous in REGEX_PRECEDERS:
                starts_regex = True
            elif previous_word in KEYWORDS_BEFORE_EXPRESSION:
                starts_regex = True
            if starts_regex is True:
                end = _skip_regex_literal(text, index)
                skips[index] = end
                _blank_span(code, index, end)
                previous = OPERAND
                previous_word = ""
                index = end
                continue

        if char == "{":
            frame["depth"] += 1
        elif char == "}":
            closes_interpolation = frame["template"] >= 0 and frame["depth"] == 0 and len(stack) > 1
            if closes_interpolation is True:
                stack.pop()
                index += 1
                continue
            frame["depth"] -= 1

        if IDENTIFIER_PATTERN.match(char) is not None:
            word = IDENTIFIER_PATTERN.match(text, index).group(0)
            previous = OPERAND
            previous_word = word
            index += len(word)
            continue

        if char.isspace() is False:
            previous = char
            previous_word = ""
        index += 1

    scan = {
        "templates": templates,
        "skips": skips,
        "comment_starts": comment_starts,
        "code": "".join(code),
    }
    return scan


def _next_significant(text: str, start: int, scan: Dict[str, Any]) -> str:
    """
        The first character at or after an offset that is neither whitespace nor part of a comment.

        :param text: The JavaScript source.
        :param start: The offset to start from.
        :param scan: The result of _scan_javascript for the text.

        :returns: The character, or "" at the end of the text.
    """
    found = ""
    index = start
    length = len(text)
    while index < length:
        if index in scan["comment_starts"]:
            index = scan["skips"][index]
            continue
        char = text[index]
        if char.isspace() is False:
            found = char
            break
        index += 1
    return found


def _expression_end(text: str, start: int, scan: Dict[str, Any], stop_at_comma: bool) -> int:
    """
        Find where the expression that starts at an offset ends.

        The expression ends at a ``;``, at a bracket that closes one opened before it, at a top-level
        comma when ``stop_at_comma`` is set, or at a line break after which the statement cannot
        continue (the code base omits statement semicolons).

        :param text: The JavaScript source.
        :param start: Offset of the first character of the expression.
        :param scan: The result of _scan_javascript for the text.
        :param stop_at_comma: Whether a comma at depth 0 ends the expression (not for call arguments).

        :returns: The offset after the expression.
    """
    end = len(text)
    depth = 0
    previous = ""
    index = start
    length = len(text)
    while index < length:
        if index in scan["skips"]:
            is_comment = index in scan["comment_starts"]
            index = scan["skips"][index]
            if is_comment is False:
                previous = OPERAND
            continue
        char = text[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                end = index
                break
            depth -= 1
        elif depth == 0 and char == ";":
            end = index
            break
        elif depth == 0 and char == "," and stop_at_comma is True:
            end = index
            break
        elif depth == 0 and char == "\n":
            following = _next_significant(text, index, scan)
            continues = previous == "" or previous in EXPRESSION_CONTINUES_AFTER
            if continues is False and following in EXPRESSION_CONTINUES_BEFORE:
                continues = True
            if continues is False:
                end = index
                break
        if char.isspace() is False:
            previous = char
        index += 1
    return end


def _has_html_ancestor(templates: List[Dict[str, Any]], record: Dict[str, Any]) -> bool:
    """
        Whether a template literal sits inside the interpolation of an ``html``-tagged template,
        whose tag escapes its value.

        :param templates: All template records of the file.
        :param record: The template to check.

        :returns: True when an enclosing template is tagged ``html``.
    """
    found = False
    parent = record["parent"]
    while parent >= 0:
        ancestor = templates[parent]
        if ancestor["tag"] == "html":
            found = True
            break
        parent = ancestor["parent"]
    return found


def _find_markup_sink_violations(text: str) -> Tuple[List[Dict[str, Any]], int]:
    """
        Find the markup sinks (``x.innerHTML =`` / ``+=`` and ``x.insertAdjacentHTML(...)``) whose
        expression holds a template literal with ``${...}`` interpolation that is not tagged ``html``
        and not nested inside an ``html``-tagged template.

        :param text: The JavaScript source.

        :returns: The violations (``line`` of the sink, ``template_line``, ``sink`` text, ``tag``),
            and the number of sinks inspected.
    """
    scan = _scan_javascript(text)
    code = scan["code"]
    templates = scan["templates"]

    spans = []
    for match in INNER_HTML_SINK_PATTERN.finditer(code):
        expression_end = _expression_end(text, match.end(), scan, True)
        spans.append((match.start(), match.end(), expression_end))
    for match in INSERT_ADJACENT_HTML_SINK_PATTERN.finditer(code):
        arguments_end = _expression_end(text, match.end(), scan, False)
        spans.append((match.start(), match.end(), arguments_end))

    violations = []
    for sink_start, expression_start, expression_end in spans:
        for record in templates:
            inside = record["start"] >= expression_start and record["start"] < expression_end
            if inside is False:
                continue
            if record["interpolated"] is False or record["tag"] == "html":
                continue
            if _has_html_ancestor(templates, record) is True:
                continue
            sink_text = text[sink_start:min(expression_end, sink_start + 100)]
            violations.append({
                "line": _line_of(text, sink_start),
                "template_line": record["line"],
                "sink": " ".join(sink_text.split()),
                "tag": record["tag"],
            })
            break

    return violations, len(spans)


# =============================================================================
# Token and stylesheet helpers
# =============================================================================

def _defined_tokens() -> Set[str]:
    """
        The custom properties tokens.css declares (in any theme block).

        :returns: The property names, e.g. {"--mj-bg", "--mj-space-3", ...}.
    """
    text = _blank_css_comments(_read_text(TOKENS_CSS_PATH))
    names = set(DECLARATION_PATTERN.findall(text))
    return names


def _without_comments(path: str, text: str) -> str:
    """
        Blank the comments of a stylesheet or script, so documentation that mentions a property is
        not read as a use of it.

        :param path: The file path (its extension selects the comment syntax).
        :param text: The file content.

        :returns: The content with comments blanked, offsets unchanged.
    """
    if path.endswith(".css") is True:
        stripped = _blank_css_comments(text)
    else:
        scan = _scan_javascript(text)
        characters = list(text)
        for start in scan["comment_starts"]:
            _blank_span(characters, start, scan["skips"][start])
        stripped = "".join(characters)
    return stripped


def _normalize_css(text: str) -> str:
    """
        Normalise CSS for comparison: comments removed, whitespace collapsed and dropped around
        punctuation.

        :param text: CSS text.

        :returns: The normalised text.
    """
    normalized = CSS_COMMENT_PATTERN.sub("", text)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s*([{};,>])\s*", r"\1", normalized)
    normalized = re.sub(r":\s+", ":", normalized)
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    normalized = normalized.strip()
    return normalized


# =============================================================================
# Tests
# =============================================================================

def test_var_references_without_fallback_name_defined_tokens():
    """
        Every ``var(--mj-*)`` without a fallback in static/javascript and static/styles names a token
        that tokens.css defines, or a property the same file declares itself.
    """
    tokens = _defined_tokens()
    testbase.assert_true(len(tokens) > 50, api="tokens.css declares the design tokens")

    files = _list_files(JAVASCRIPT_ROOT, (".js",)) + _list_files(STYLES_ROOT, (".css",))
    reference_count = 0
    undefined = []
    for path in files:
        text = _without_comments(path, _read_text(path))
        declared_here = set(DECLARATION_PATTERN.findall(text))
        declared_here.update(SET_PROPERTY_PATTERN.findall(text))
        for match in VAR_REFERENCE_PATTERN.finditer(text):
            reference_count += 1
            name = match.group(1)
            has_fallback = match.group(2) == ","
            if has_fallback is True:
                continue
            if name in tokens or name in declared_here:
                continue
            undefined.append(f"{_relative_name(path)}:{_line_of(text, match.start())}: var({name}) "
                             f"has no fallback and {name} is not defined in styles/tokens.css")

    testbase.assert_true(reference_count >= MINIMUM_EXPECTED_VAR_REFERENCES,
                         api=f"the scan found {reference_count} var(--mj-*) references")
    testbase.assert_equal(undefined, [], api="var(--mj-*) references without a fallback")
    return


def test_base_css_matches_basestyles_js():
    """
        styles/base.css and the BASE_CSS string in core/basestyles.js hold the same rules after
        comments and whitespace are stripped.
    """
    stylesheet = _normalize_css(_read_text(BASE_CSS_PATH))

    script = _read_text(BASESTYLES_JS_PATH)
    match = BASE_CSS_STRING_PATTERN.search(script)
    testbase.assert_true(match is not None, api="core/basestyles.js declares `const BASE_CSS = `...`;`")
    embedded = _normalize_css(match.group(1))

    if stylesheet != embedded:
        stylesheet_rules = stylesheet.replace("}", "}\n").splitlines()
        embedded_rules = embedded.replace("}", "}\n").splitlines()
        difference = difflib.unified_diff(stylesheet_rules, embedded_rules, fromfile="styles/base.css",
                                          tofile="javascript/core/basestyles.js BASE_CSS", lineterm="")
        errmsg = "base.css and BASE_CSS differ (normalised rules):\n" + "\n".join(difference)
        raise AssertionError(errmsg)
    return


def test_markup_sinks_take_no_untagged_interpolated_templates():
    """
        No ``innerHTML`` assignment or ``insertAdjacentHTML`` call in static/javascript takes a template
        literal with ``${...}`` interpolation that does not come from the ``html`` tag of core/html.js.
    """
    sink_count = 0
    violations = []
    for path in _list_files(JAVASCRIPT_ROOT, (".js",)):
        found, inspected = _find_markup_sink_violations(_read_text(path))
        sink_count += inspected
        for violation in found:
            violations.append(f"{_relative_name(path)}:{violation['line']}: {violation['sink']} "
                              f"(template at line {violation['template_line']}, "
                              f"tag {violation['tag'] or '(none)'})")

    testbase.assert_true(sink_count >= MINIMUM_EXPECTED_SINKS,
                         api=f"the scan found {sink_count} innerHTML / insertAdjacentHTML sinks")
    testbase.assert_equal(violations, [], api="markup sinks given an untagged interpolated template")
    return


def test_markup_sink_scan_flags_untagged_interpolated_templates():
    """
        The sink scan used above reports an untagged interpolated template and accepts the safe forms,
        so the library check cannot pass because the scanner missed a sink.
    """
    source = "\n".join([
        "// el.innerHTML = `<b>${commented}</b>`",
        "const pattern = /`${notATemplate}`/g",
        "a.innerHTML = String(html`<b>${name}</b>`)",
        "b.innerHTML = `<svg viewBox=\"0 0 16 16\"></svg>`",
        "c.innerHTML = html`<ul>${items.map((item) => html`<li>${item}</li>`)}</ul>`",
        "d.innerHTML = `<b>${name}</b>`",
        "e.innerHTML =",
        "  open === true",
        "    ? `<i>${label}</i>`",
        "    : \"\"",
        "f.insertAdjacentHTML(\"beforeend\", `<li>${item}</li>`)",
        "g.innerHTML = html`<p>${`raw ${text}`}</p>`",
        "h.innerHTML += `<hr data-x=\"${value}\">`",
    ])
    violations, inspected = _find_markup_sink_violations(source)
    flagged_lines = [violation["line"] for violation in violations]

    testbase.assert_equal(inspected, 8, api="sinks found in the sample (the commented one excluded)")
    testbase.assert_equal(flagged_lines, [6, 7, 13, 11], api="lines of the flagged sinks")
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
