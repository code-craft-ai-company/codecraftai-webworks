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
