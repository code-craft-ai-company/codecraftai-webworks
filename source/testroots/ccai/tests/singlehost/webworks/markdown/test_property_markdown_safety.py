"""
    Property tests for the safety of rendered markdown.

    Whatever text is given, the renderer finishes, and the only markup in its HTML is the markup it writes itself: every
    ``<`` starts one of its own tags, and no destination it writes has an unsafe scheme.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import re

from ccai import testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.webworks.markdown import MarkdownRenderer, is_safe_url

#: Characters that make markdown structure, plus letters, digits and the characters HTML cares about.
MARKDOWN_TEXT_ALPHABET = "abcxyz019 \n\t#*_~`[]()!<>&\"'|:-+=.\\/"

#: The tags the renderer writes.
RENDERED_TAG_PATTERN = re.compile(
    r"</?(?:h[1-6]|p|em|strong|del|code|pre|blockquote|ul|ol|li|table|thead|tbody|tr|th|td|a|img|hr|br)\b"
)

#: A link or image address in the rendered HTML.
RENDERED_ADDRESS_PATTERN = re.compile(r'(?:href|src)="([^"]*)"')


@given(text=st.text(alphabet=MARKDOWN_TEXT_ALPHABET, max_size=200), constraints={"max_examples": 300})
def test_every_angle_bracket_in_the_html_starts_a_tag_the_renderer_writes(text: str):
    """
        **Feature: markdown safety**
        **Property: for any text, rendering finishes and each ``<`` in the HTML opens or closes one of the renderer's own tags, so markup in the text can
        never reach the page as markup.**
    """
    html = MarkdownRenderer().render(text).html

    foreign = []
    for match in re.finditer("<", html):
        position = match.start()
        if RENDERED_TAG_PATTERN.match(html, position) is None:
            foreign.append(html[position:position + 20])

    testbase.assert_equal(foreign, [], "The HTML holds markup the renderer did not write: {!r}".format(html))
    return


@given(
    scheme=st.sampled_from(["javascript", "JavaScript", "vbscript", "data", "java\tscript", " javascript", "file"]),
    payload=st.text(alphabet="abc()1:/;,", max_size=20),
    constraints={"max_examples": 100},
)
def test_no_link_or_image_is_written_with_an_unsafe_scheme(scheme: str, payload: str):
    """
        **Feature: markdown safety**
        **Property: a link, an autolink or an image whose destination has an unsafe scheme, in any case and with ignored characters inside it, is never
        written as an ``href`` or ``src``.**
    """
    destination = "{}:{}".format(scheme, payload)
    text = "[link](<{0}>) ![image](<{0}>) <{0}>".format(destination)
    html = MarkdownRenderer().render(text).html

    unsafe = []
    for address in RENDERED_ADDRESS_PATTERN.findall(html):
        if not is_safe_url(address):
            unsafe.append(address)
        if address.lower().replace("%09", "").replace("%20", "").startswith(("javascript", "vbscript", "data:", "file:")):
            unsafe.append(address)

    testbase.assert_equal(unsafe, [], "An unsafe destination was written: {!r}".format(html))
    return
