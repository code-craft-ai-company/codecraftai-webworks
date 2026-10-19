"""
    Serves a folder of markdown books with the webworks development server.

    The folder's ``README.md`` is the library index: it links to the books, and each book's index links to its
    documents. Usage::

        python source/examples/books/serve_books.py ~/repos/codecraftai-books --port 8000

    then open http://127.0.0.1:8000/books/ in a browser.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import argparse
import os
import sys

from ccai.webworks.books import BookLibrary, BooksBlueprint
from ccai.webworks.devexp.server.devserver import DevelopmentServer
from ccai.webworks.webapplication import establish_webapp_persona
from ccai.webworks.wellknown import ThisWebApplicationSingleton


def main() -> int:
    """
        Reads the command line, builds the web application and serves the library until interrupted.

        :returns: The process exit code.
    """
    parser = argparse.ArgumentParser(description="Serve a folder of markdown books as HTML pages.")
    parser.add_argument("library", help="The folder that holds the library; its README.md is the library index.")
    parser.add_argument("--index", default="README.md", help="The library index document, from the folder (default: README.md).")
    parser.add_argument("--title", default=None, help="The library's title (default: the index document's title).")
    parser.add_argument("--mount", default="/books", help="The URL path the library is served under (default: /books).")
    parser.add_argument("--host", default="127.0.0.1", help="The address to listen on (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="The port to listen on (default: 8000).")
    args = parser.parse_args()

    presence_dir = os.path.join(".output", "examples", "books")
    webapp = establish_webapp_persona(name="books", logger_name="books", log_basename="books", presence_dir=presence_dir)

    library = BookLibrary(args.library, index_document=args.index, title=args.title)
    books = BooksBlueprint(library, mount_path=args.mount)
    books.attach_to_webapp(webapp)

    webapp.startup()
    app = ThisWebApplicationSingleton().asgi_app

    print("Serving {} at http://{}:{}{}".format(library.root_dir, args.host, args.port, books.library_url()))

    server = DevelopmentServer(app=app, debug=True, reload=False)
    server.serve_forever(host=args.host, port=args.port)

    exit_code = 0
    return exit_code


if __name__ == "__main__":
    status = main()
    sys.exit(status)
