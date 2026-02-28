"""
    Colored output utilities for the webworks CLI.

    This module provides ANSI color support for terminal output with
    automatic detection of terminal capabilities. Colors are disabled
    when the output is not a TTY, when the ``NO_COLOR`` environment
    variable is set, or when explicitly turned off.

    The module exposes individual color constants, a general-purpose
    :func:`colorize` function, and convenience functions for common
    semantic output categories such as :func:`success`, :func:`error`,
    :func:`warning`, and :func:`info`.
"""

import os
import sys

from typing import Optional


# =============================================================================
# ANSI Color Code Constants
# =============================================================================

ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"
ANSI_WHITE = "\033[37m"
ANSI_RESET = "\033[0m"

COLOR_MAP = {
    "red": ANSI_RED,
    "green": ANSI_GREEN,
    "yellow": ANSI_YELLOW,
    "blue": ANSI_BLUE,
    "magenta": ANSI_MAGENTA,
    "cyan": ANSI_CYAN,
    "white": ANSI_WHITE,
    "reset": ANSI_RESET,
}


# =============================================================================
# Terminal Detection
# =============================================================================

def is_color_supported(stream: Optional[object] = None) -> bool:
    """
        Determine whether the given output stream supports ANSI colors.

        Color is considered supported when all of the following are true:

        1. The ``NO_COLOR`` environment variable is **not** set.
        2. The stream has an ``isatty`` method that returns ``True``.

        When *stream* is ``None`` the check is performed against
        :data:`sys.stdout`.

        :param stream: The output stream to check.  Defaults to
            ``sys.stdout`` when ``None``.

        :returns: ``True`` if the stream supports color output.
    """
    no_color_env = os.environ.get("NO_COLOR")
    if no_color_env is not None:
        return False

    if stream is None:
        stream = sys.stdout

    is_tty_callable = hasattr(stream, "isatty") and callable(stream.isatty)
    if not is_tty_callable:
        return False

    is_tty = stream.isatty()

    return is_tty


# =============================================================================
# Colorize Function
# =============================================================================

def colorize(text: str, color: str, stream: Optional[object] = None) -> str:
    """
        Wrap *text* with the ANSI escape sequence for *color*.

        If the terminal does not support colors the original *text* is
        returned unchanged.  The *color* name is looked up in
        :data:`COLOR_MAP` (case-insensitive).  An unrecognised color
        name causes the plain text to be returned.

        :param text: The text to colorize.
        :param color: The color name (e.g. ``"red"``, ``"green"``).
        :param stream: Optional output stream used for the TTY check.

        :returns: The colorized string, or the original text when
            colors are not supported.
    """
    color_enabled = is_color_supported(stream=stream)
    if not color_enabled:
        return text

    color_lower = color.lower()
    ansi_code = COLOR_MAP.get(color_lower)

    if ansi_code is None:
        return text

    result = "{}{}{}".format(ansi_code, text, ANSI_RESET)

    return result


# =============================================================================
# Convenience Functions
# =============================================================================

def success(text: str, stream: Optional[object] = None) -> str:
    """
        Return *text* colored green to indicate success.

        :param text: The text to colorize.
        :param stream: Optional output stream used for the TTY check.

        :returns: The green-colored string, or plain text when colors
            are not supported.
    """
    result = colorize(text, "green", stream=stream)

    return result


def error(text: str, stream: Optional[object] = None) -> str:
    """
        Return *text* colored red to indicate an error.

        :param text: The text to colorize.
        :param stream: Optional output stream used for the TTY check.

        :returns: The red-colored string, or plain text when colors
            are not supported.
    """
    result = colorize(text, "red", stream=stream)

    return result


def warning(text: str, stream: Optional[object] = None) -> str:
    """
        Return *text* colored yellow to indicate a warning.

        :param text: The text to colorize.
        :param stream: Optional output stream used for the TTY check.

        :returns: The yellow-colored string, or plain text when colors
            are not supported.
    """
    result = colorize(text, "yellow", stream=stream)

    return result


def info(text: str, stream: Optional[object] = None) -> str:
    """
        Return *text* colored cyan to indicate informational output.

        :param text: The text to colorize.
        :param stream: Optional output stream used for the TTY check.

        :returns: The cyan-colored string, or plain text when colors
            are not supported.
    """
    result = colorize(text, "cyan", stream=stream)

    return result
