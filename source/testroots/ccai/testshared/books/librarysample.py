"""
    A small library of markdown books, written to a folder for the books tests.

    The library is laid out so that folder structure and navigation disagree: one chapter sits in the ``chapters`` folder
    but no index links to it, an appendix sits outside the ``chapters`` folder but the index links to it, and the second
    volume's index is ``index.md`` rather than ``README.md``.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import os

from typing import Dict

#: The bytes of the sample image (a PNG signature is enough for the tests).
SAMPLE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8

#: The markdown files of the sample library, by location.
SAMPLE_LIBRARY_FILES: Dict[str, str] = {
    "README.md": (
        "# The Library\n"
        "\n"
        "| Volume | Status |\n"
        "|---|---|\n"
        "| [First Volume](volumes/one/) | drafted |\n"
        "| [Second Volume](volumes/two/index.md) | planned |\n"
        "\n"
        "The [series plan](series.md) explains the order. [GitHub](https://github.com/code-craft-ai-company) hosts the sources.\n"
    ),
    "series.md": "# Series Plan\n\nRead [the first volume](volumes/one/README.md) first.\n",
    "volumes/one/README.md": (
        "# Volume One\n"
        "\n"
        "[Back to the library](../../README.md)\n"
        "\n"
        "| Chapter | Status |\n"
        "|---|---|\n"
        "| [Getting Started](chapters/01-start.md) | drafted |\n"
        "| [Going Further](chapters/02-further.md#details) | drafted |\n"
        "\n"
        "- [Appendix A](appendix/a.md)\n"
        "- [Getting Started, again](chapters/01-start.md)\n"
        "- [The figure](figures/diagram.png)\n"
    ),
    "volumes/one/chapters/01-start.md": (
        "# Getting Started\n"
        "\n"
        "## Setup\n"
        "\n"
        "![Diagram](../figures/diagram.png)\n"
        "\n"
        "Continue with [going further](02-further.md#details), see [the series](/series.md) or read "
        "[the code](../../../../elsewhere/code.py).\n"
        "\n"
        "### Details of setup\n"
    ),
    "volumes/one/chapters/02-further.md": "# Going Further\n\n## Details\n\nText.\n",
    "volumes/one/chapters/99-unlisted.md": "# Unlisted\n\nNo index links here.\n",
    "volumes/one/appendix/a.md": "# Appendix A\n",
    "volumes/two/index.md": "# Volume Two\n\n1. [The Only Chapter](only.md)\n",
    "volumes/two/only.md": "# Only\n",
    ".hidden/secret.md": "# Secret\n",
    "notes.txt": "Not a document.\n",
}


def write_sample_library(root: str) -> None:
    """
        Writes the sample library into a folder.

        :param root: The folder.
    """
    for location, text in SAMPLE_LIBRARY_FILES.items():
        path = os.path.join(root, *location.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as sample_file:
            sample_file.write(text)

    image_path = os.path.join(root, "volumes", "one", "figures", "diagram.png")
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, "wb") as image_file:
        image_file.write(SAMPLE_IMAGE_BYTES)

    return
