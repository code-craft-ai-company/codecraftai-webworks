"""
    Tests for the webworks CLI colored output module.

    This module contains unit tests for terminal color detection,
    the colorize function, and the convenience functions for
    semantic output categories (success, error, warning, info).
"""

import os

from automojo.webworks.devexp.cli.output import (
    ANSI_BLUE,
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_MAGENTA,
    ANSI_RED,
    ANSI_RESET,
    ANSI_WHITE,
    ANSI_YELLOW,
    COLOR_MAP,
    colorize,
    error,
    info,
    is_color_supported,
    success,
    warning,
)


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeTTYStream:
    """
        A fake stream that reports itself as a TTY.
    """

    def isatty(self) -> bool:
        """
            Report that this stream is a TTY.

            :returns: Always ``True``.
        """
        return True


class _FakeNonTTYStream:
    """
        A fake stream that reports itself as not a TTY.
    """

    def isatty(self) -> bool:
        """
            Report that this stream is not a TTY.

            :returns: Always ``False``.
        """
        return False


class _FakeNoIsattyStream:
    """
        A fake stream that does not have an isatty method.
    """
    pass


def _with_no_color_env(func):
    """
        Run *func* with the NO_COLOR environment variable set.

        Saves and restores the original value of NO_COLOR around
        the call.

        :param func: A callable to invoke with NO_COLOR set.

        :returns: The return value of *func*.
    """
    original = os.environ.get("NO_COLOR")

    try:
        os.environ["NO_COLOR"] = "1"
        result = func()
    finally:
        if original is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = original

    return result


def _without_no_color_env(func):
    """
        Run *func* with the NO_COLOR environment variable removed.

        Saves and restores the original value of NO_COLOR around
        the call.

        :param func: A callable to invoke without NO_COLOR.

        :returns: The return value of *func*.
    """
    original = os.environ.get("NO_COLOR")

    try:
        os.environ.pop("NO_COLOR", None)
        result = func()
    finally:
        if original is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = original

    return result


# =============================================================================
# Unit Tests for ANSI Constants
# =============================================================================

def test_ansi_reset_is_escape_sequence():
    """
        Test that ANSI_RESET contains the expected escape sequence.
    """
    if ANSI_RESET != "\033[0m":
        errmsg = "Expected ANSI_RESET to be '\\033[0m', got '{}'".format(repr(ANSI_RESET))
        raise AssertionError(errmsg)

    return


def test_color_map_contains_all_colors():
    """
        Test that COLOR_MAP contains entries for all expected color names.
    """
    expected_colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white", "reset"]

    for color_name in expected_colors:
        if color_name not in COLOR_MAP:
            errmsg = "Expected '{}' in COLOR_MAP".format(color_name)
            raise AssertionError(errmsg)

    return


def test_color_map_red_matches_constant():
    """
        Test that COLOR_MAP['red'] matches the ANSI_RED constant.
    """
    if COLOR_MAP["red"] != ANSI_RED:
        errmsg = "Expected COLOR_MAP['red'] to equal ANSI_RED"
        raise AssertionError(errmsg)

    return


def test_color_map_green_matches_constant():
    """
        Test that COLOR_MAP['green'] matches the ANSI_GREEN constant.
    """
    if COLOR_MAP["green"] != ANSI_GREEN:
        errmsg = "Expected COLOR_MAP['green'] to equal ANSI_GREEN"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for is_color_supported
# =============================================================================

def test_is_color_supported_returns_true_for_tty():
    """
        Test that is_color_supported returns True for a TTY stream
        when NO_COLOR is not set.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return is_color_supported(stream=tty_stream)

    result = _without_no_color_env(check)

    if result is not True:
        errmsg = "Expected True for TTY stream, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_is_color_supported_returns_false_for_non_tty():
    """
        Test that is_color_supported returns False for a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()

    def check():
        return is_color_supported(stream=non_tty_stream)

    result = _without_no_color_env(check)

    if result is not False:
        errmsg = "Expected False for non-TTY stream, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_is_color_supported_returns_false_when_no_isatty():
    """
        Test that is_color_supported returns False when the stream
        does not have an isatty method.
    """
    no_isatty_stream = _FakeNoIsattyStream()

    def check():
        return is_color_supported(stream=no_isatty_stream)

    result = _without_no_color_env(check)

    if result is not False:
        errmsg = "Expected False for stream without isatty, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_is_color_supported_returns_false_when_no_color_set():
    """
        Test that is_color_supported returns False when the NO_COLOR
        environment variable is set, even for a TTY stream.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return is_color_supported(stream=tty_stream)

    result = _with_no_color_env(check)

    if result is not False:
        errmsg = "Expected False when NO_COLOR is set, got {}".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for colorize
# =============================================================================

def test_colorize_wraps_text_with_color_on_tty():
    """
        Test that colorize wraps text with ANSI codes on a TTY stream.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return colorize("hello", "red", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}hello{}".format(ANSI_RED, ANSI_RESET)

    if result != expected:
        errmsg = "Expected '{}', got '{}'".format(repr(expected), repr(result))
        raise AssertionError(errmsg)

    return


def test_colorize_returns_plain_text_on_non_tty():
    """
        Test that colorize returns plain text on a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()

    def check():
        return colorize("hello", "red", stream=non_tty_stream)

    result = _without_no_color_env(check)

    if result != "hello":
        errmsg = "Expected plain 'hello', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_colorize_returns_plain_text_when_no_color_set():
    """
        Test that colorize returns plain text when NO_COLOR is set.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return colorize("hello", "green", stream=tty_stream)

    result = _with_no_color_env(check)

    if result != "hello":
        errmsg = "Expected plain 'hello' with NO_COLOR set, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_colorize_returns_plain_text_for_unknown_color():
    """
        Test that colorize returns plain text for an unrecognised color name.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return colorize("hello", "neon_pink", stream=tty_stream)

    result = _without_no_color_env(check)

    if result != "hello":
        errmsg = "Expected plain 'hello' for unknown color, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_colorize_is_case_insensitive():
    """
        Test that colorize accepts color names in any case.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return colorize("hello", "RED", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}hello{}".format(ANSI_RED, ANSI_RESET)

    if result != expected:
        errmsg = "Expected case-insensitive match, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_colorize_handles_empty_text():
    """
        Test that colorize handles an empty string correctly.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return colorize("", "blue", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}{}".format(ANSI_BLUE, ANSI_RESET)

    if result != expected:
        errmsg = "Expected colored empty string, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_colorize_all_supported_colors():
    """
        Test that colorize works for every color in COLOR_MAP.
    """
    tty_stream = _FakeTTYStream()

    color_names = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]

    for color_name in color_names:
        ansi_code = COLOR_MAP[color_name]

        def check(cn=color_name):
            return colorize("test", cn, stream=tty_stream)

        result = _without_no_color_env(check)
        expected = "{}test{}".format(ansi_code, ANSI_RESET)

        if result != expected:
            errmsg = "Color '{}': expected '{}', got '{}'".format(
                color_name, repr(expected), repr(result)
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Convenience Functions
# =============================================================================

def test_success_returns_green_text_on_tty():
    """
        Test that success() returns green-colored text on a TTY stream.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return success("ok", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}ok{}".format(ANSI_GREEN, ANSI_RESET)

    if result != expected:
        errmsg = "Expected green 'ok', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_success_returns_plain_text_on_non_tty():
    """
        Test that success() returns plain text on a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()

    def check():
        return success("ok", stream=non_tty_stream)

    result = _without_no_color_env(check)

    if result != "ok":
        errmsg = "Expected plain 'ok', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_error_returns_red_text_on_tty():
    """
        Test that error() returns red-colored text on a TTY stream.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return error("fail", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}fail{}".format(ANSI_RED, ANSI_RESET)

    if result != expected:
        errmsg = "Expected red 'fail', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_error_returns_plain_text_on_non_tty():
    """
        Test that error() returns plain text on a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()

    def check():
        return error("fail", stream=non_tty_stream)

    result = _without_no_color_env(check)

    if result != "fail":
        errmsg = "Expected plain 'fail', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_warning_returns_yellow_text_on_tty():
    """
        Test that warning() returns yellow-colored text on a TTY stream.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return warning("caution", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}caution{}".format(ANSI_YELLOW, ANSI_RESET)

    if result != expected:
        errmsg = "Expected yellow 'caution', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_warning_returns_plain_text_on_non_tty():
    """
        Test that warning() returns plain text on a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()

    def check():
        return warning("caution", stream=non_tty_stream)

    result = _without_no_color_env(check)

    if result != "caution":
        errmsg = "Expected plain 'caution', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_info_returns_cyan_text_on_tty():
    """
        Test that info() returns cyan-colored text on a TTY stream.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return info("note", stream=tty_stream)

    result = _without_no_color_env(check)
    expected = "{}note{}".format(ANSI_CYAN, ANSI_RESET)

    if result != expected:
        errmsg = "Expected cyan 'note', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_info_returns_plain_text_on_non_tty():
    """
        Test that info() returns plain text on a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()

    def check():
        return info("note", stream=non_tty_stream)

    result = _without_no_color_env(check)

    if result != "note":
        errmsg = "Expected plain 'note', got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for NO_COLOR with Convenience Functions
# =============================================================================

def test_success_returns_plain_text_when_no_color_set():
    """
        Test that success() returns plain text when NO_COLOR is set.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return success("ok", stream=tty_stream)

    result = _with_no_color_env(check)

    if result != "ok":
        errmsg = "Expected plain 'ok' with NO_COLOR, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_error_returns_plain_text_when_no_color_set():
    """
        Test that error() returns plain text when NO_COLOR is set.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return error("fail", stream=tty_stream)

    result = _with_no_color_env(check)

    if result != "fail":
        errmsg = "Expected plain 'fail' with NO_COLOR, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_warning_returns_plain_text_when_no_color_set():
    """
        Test that warning() returns plain text when NO_COLOR is set.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return warning("caution", stream=tty_stream)

    result = _with_no_color_env(check)

    if result != "caution":
        errmsg = "Expected plain 'caution' with NO_COLOR, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_info_returns_plain_text_when_no_color_set():
    """
        Test that info() returns plain text when NO_COLOR is set.
    """
    tty_stream = _FakeTTYStream()

    def check():
        return info("note", stream=tty_stream)

    result = _with_no_color_env(check)

    if result != "note":
        errmsg = "Expected plain 'note' with NO_COLOR, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return
