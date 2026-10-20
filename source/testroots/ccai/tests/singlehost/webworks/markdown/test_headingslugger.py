"""
    Tests for the anchors given to headings.

    Anchors follow GitHub's rules, so ``#fragment`` links written against a repository keep working on the site.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from ccai import testbase

from ccai.webworks.markdown import HeadingSlugger, make_heading_slug


def test_a_slug_is_lower_case_with_hyphens_for_spaces_and_no_punctuation():
    """
        **Feature: heading anchors**
        **Property: letters and digits are lowered and kept (in any script), spaces become hyphens one for one, hyphens and underscores are kept, and
        other punctuation and symbols are removed.**
    """
    testbase.assert_equal(
        (
            make_heading_slug("Appendix Volume — Operating a Platform"),
            make_heading_slug("What's `new` in 2.0?"),
            make_heading_slug("snake_case and kebab-case"),
            make_heading_slug("Überblick über Ü"),
        ),
        (
            "appendix-volume--operating-a-platform",
            "whats-new-in-20",
            "snake_case-and-kebab-case",
            "überblick-über-ü",
        ),
    )
    return


def test_repeated_slugs_are_numbered_and_never_collide():
    """
        **Feature: heading anchors**
        **Property: a repeated heading gets ``-1``, ``-2`` and so on; a number already taken by a heading whose own text ends that way is skipped; a heading
        with no letters or digits is ``section``.**
    """
    slugger = HeadingSlugger()
    slugs = [slugger.slug("Intro"), slugger.slug("Intro-1"), slugger.slug("Intro"), slugger.slug("Intro"), slugger.slug("!!!")]
    testbase.assert_equal(slugs, ["intro", "intro-1", "intro-2", "intro-3", "section"])
    return
