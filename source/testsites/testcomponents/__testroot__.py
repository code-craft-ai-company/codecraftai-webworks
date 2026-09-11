"""
    Marks 'testcomponents' as a testbase test root.

    The functional site suite lives in the 'tests' package beside this file and is
    collected with '--root ./source/testsites/testcomponents --includes=testcomponents.tests'.
    Placing the marker here, rather than inside 'tests', keeps the suite's modules under
    their real import name ('testcomponents.tests.<module>'), which is what the
    repository's PYTHONPATH already resolves.
"""

ROOT_TYPE = "testbase"
