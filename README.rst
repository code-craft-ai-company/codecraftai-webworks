====================
codecraftai-webworks
====================

Code Craft AI - WebWorks

Overview
========
codecraftai-webworks is a core component of the Code Craft AI technology stack. It provides robust, reusable foundation code designed to enable and orchestrate complex software automation tasks.

Installation
============
Using Poetry:

.. code-block:: bash

    poetry add codecraftai-webworks

Markdown Books
==============
``BooksBlueprint`` serves a folder of markdown books as HTML pages. Navigation comes from the links in the markdown,
not from the folders the files are in: the library's index document (``README.md`` at the root) links to the books,
each book's index document links to its chapters, and the order of those links, in lists or tables, is the reading
order. The text of each link is the title the navigation shows. A link to a folder means the folder's ``README.md``
(or ``index.md``).

.. code-block:: python

    from ccai.webworks.books import BookLibrary, BooksBlueprint

    library = BookLibrary("~/repos/codecraftai-books")
    books = BooksBlueprint(library, mount_path="/books")
    books.attach_to_webapp(webapp)

Each page shows its book's contents, breadcrumbs, links to the previous and next documents and an outline of its
headings. Links between the markdown files are rewritten to the URLs the documents are served at, and images in the
library are served beside them. Nothing outside the library's folder, and no hidden file, is ever served. Pages carry
a Content-Security-Policy that allows no script.

The markdown is rendered by ``ccai.webworks.markdown`` (no third-party library): CommonMark plus GitHub tables,
strikethrough and links made from bare addresses. Raw HTML in the markdown is escaped and links with unsafe schemes
such as ``javascript:`` are dropped.

To read a library with the development server:

.. code-block:: bash

    python source/examples/books/serve_books.py ~/repos/codecraftai-books --port 8000

Development
===========
This repository provides a standard Poetry environment.

1. Activate virtual environment:
   Run `poetry shell` and `poetry install`
2. Test Execution:
   Tests run under the `testbase` runner. The single-host suite:

   .. code-block:: bash

       testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output/

   The functional site suite for the testcomponents site (needs Playwright and
   its Chromium browser; skipped cleanly without them):

   .. code-block:: bash

       testbase testing run --root ./source/testsites/testcomponents --includes=testcomponents.tests --output=./.output/testcomponents-tests

References
==========
- `User Guide <userguide/userguide.rst>`
- `Coding Standards <userguide/10-00-coding-standards.rst>`
