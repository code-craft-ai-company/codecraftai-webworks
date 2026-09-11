"""
    .. module:: testcomponents.harness.generation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Defines one module-level test per catalog entry.

    The sweeps over "every component" and "every chart type" are table driven.
    Under testbase each case becomes its own module-level
    ``test_*`` function, so a broken component is reported by name rather than as
    one failure inside a 139-case loop. :func:`define_page_tests` builds those
    functions from a check function and a case table, in the calling module's
    namespace, and attaches the per-test ``page`` resource to each.
"""

from typing import Any, Callable, Dict, List, Sequence, Tuple

import ccai.testbase as testbase

from ccai.errors.exceptions import SemanticError

from testcomponents.harness.factories import create_page


def define_page_tests(namespace: Dict[str, Any], basename: str,
                      check: Callable[..., None],
                      cases: Sequence[Tuple[str, Tuple[Any, ...]]]) -> List[str]:
    """
        Define one ``test_*`` function per case in the given module namespace.

        Each generated function takes ``(page, base_url)``, has the ``page``
        resource attached, and calls ``check(page, base_url, *case_arguments)``.
        Its name is ``"<basename>__<case identifier>"``.

        :param namespace: The defining module's ``globals()``.
        :param basename: The ``test_``-prefixed base name shared by the cases.
        :param check: The check to run, taking ``(page, base_url, *case_arguments)``.
        :param cases: ``(case_identifier, case_arguments)`` pairs, one per test.

        :returns: The names of the functions defined, in case order.

        :raises SemanticError: When ``basename`` is not ``test_``-prefixed, or a
            generated name collides with something already in the namespace.
    """

    if not basename.startswith("test_"):
        raise SemanticError(
            "define_page_tests requires a 'test_' prefixed basename, got {!r}.".format(basename))

    module_name = namespace["__name__"]

    defined = []
    for case_identifier, case_arguments in cases:
        test_name = "{}__{}".format(basename, case_identifier)
        if test_name in namespace:
            raise SemanticError(
                "define_page_tests would redefine {}.{}; case identifiers must be unique.".format(
                    module_name, test_name))

        test_function = _make_page_test(module_name, test_name, check, case_arguments)
        namespace[test_name] = test_function
        defined.append(test_name)

    return defined


def _make_page_test(module_name: str, test_name: str, check: Callable[..., None],
                    case_arguments: Tuple[Any, ...]) -> Callable[[Any, str], None]:
    """
        Build one generated test function.

        :param module_name: The defining module's name; the collector only accepts
            functions whose ``__module__`` is the module it found them in.
        :param test_name: The function name.
        :param check: The check the function runs.
        :param case_arguments: The case's arguments, passed after ``page`` and ``base_url``.

        :returns: The test function, with the ``page`` resource attached.
    """

    def page_test(page: Any, base_url: str) -> None:
        check(page, base_url, *case_arguments)
        return

    page_test.__name__ = test_name
    page_test.__qualname__ = test_name
    page_test.__module__ = module_name
    page_test.__doc__ = "{}\n\n        Case: {!r}\n".format(
        (check.__doc__ or "").rstrip(), case_arguments)

    testbase.attach.parameter(create_page, identifier="page")(page_test)

    return page_test
