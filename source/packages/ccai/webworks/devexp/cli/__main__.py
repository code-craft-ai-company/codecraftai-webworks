"""
    Module entry point for the webworks CLI.

    Lets the command line be run without the console script::

        python -m ccai.webworks.devexp.cli serve --app app:app
"""

import sys

from ccai.webworks.devexp.cli.webworkscli import main


if __name__ == "__main__":
    sys.exit(main())
