"""
    pytest adapter for tests decorated with
    :func:`ccai.testbase.properties.given`.

    The ``ccai.testbase.properties`` framework ships a ``given``
    decorator that stamps a ``_property_`` attribute on a test
    function carrying the strategy bindings and execution
    constraints. It is intended to be invoked by the TestBase test
    sequencer, which detects the marker, generates inputs from the
    declared strategies, and runs the function once per generated
    example.

    Webworks runs its test suite under pytest, not under the
    TestBase sequencer. Without an adapter, pytest sees the test
    function's strategy-bound parameter (e.g. ``scope_names``),
    tries to inject it as a fixture, and fails collection with
    ``fixture 'scope_names' not found``. The result is a silent
    family of test errors that nobody catches in CI because pytest
    treats them as collection errors rather than test failures.

    This conftest closes the gap with a single
    :func:`pytest_generate_tests` hook:

      1. Detect functions tagged with ``_property_``.
      2. Generate ``max_examples`` random inputs from the declared
         strategies, using a deterministic seed derived from the
         fully-qualified test name (matches the reproducibility
         contract documented on
         :class:`ccai.testbase.properties.PropertyRunner`).
      3. Parametrise the test once per generated example.

    Each example becomes a separate pytest invocation, so failures
    point at the specific input that broke and the suite reports
    ``examples * tests`` results rather than one aggregated
    pass / fail per property.

    Tests can short-circuit invalid example inputs via
    :func:`ccai.testbase.properties.assume`, which raises
    :class:`UnsatisfiedAssumption`. The :func:`pytest_runtest_call`
    hook below converts that exception into a ``pytest.skip`` so an
    assumption-rejected example is reported as skipped rather than
    errored.

    Counterexample shrinking — the other half of TestBase's
    PropertyRunner — is **not** implemented here. When a property
    fails under pytest, the failing example shows up as-is. Devs
    can still debug from the parametrize id (``example_NN``) and
    the seed.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import hashlib
import random

from typing import Any

import pytest

from ccai.testbase.properties.assumptions import UnsatisfiedAssumption


def _derive_test_seed(test_name: str) -> int:
    """
        Derive a deterministic 64-bit seed from a fully-qualified
        test name.

        Matches the seed-derivation contract documented on
        :func:`ccai.testbase.properties.propertyrunner.derive_test_seed`
        so the same test produces the same example values whether
        run via the TestBase sequencer or through this adapter.
        TestBase's version mixes the job seed in too; the pytest
        adapter has no job-seed concept, so the test name is the
        sole input.

        :param test_name: Fully-qualified test name
                          (``module.qualname``).

        :returns: 64-bit integer suitable for seeding
                  :class:`random.Random`.
    """
    seed_source = test_name.encode("utf-8")
    digest = hashlib.sha256(seed_source).digest()

    rtnval = int.from_bytes(digest[:8], byteorder="big")
    return rtnval


def pytest_generate_tests(metafunc: Any) -> None:
    """
        Translate ``@given``-decorated tests into ``parametrize``
        invocations.

        :param metafunc: The pytest ``Metafunc`` for the test under
                         collection.
    """
    func = metafunc.function
    property_meta = getattr(func, "_property_", None)
    if property_meta is None:
        return

    strategies = property_meta.get("strategies", {})
    if len(strategies) == 0:
        return

    constraints = property_meta.get("constraints", {})
    max_examples = constraints.get("max_examples", 100)

    if not isinstance(max_examples, int) or max_examples <= 0:
        return

    test_name = "{}.{}".format(func.__module__, func.__qualname__)
    seed = _derive_test_seed(test_name)
    rng = random.Random(seed)

    parameter_names = list(strategies.keys())

    examples: list = []
    ids: list = []
    for index in range(max_examples):
        values = tuple(strategies[name].generate(rng) for name in parameter_names)
        examples.append(values)
        ids.append("example_{:04d}".format(index))

    metafunc.parametrize(parameter_names, examples, ids=ids)
    return


def pytest_runtest_call(item: Any) -> None:
    """
        Translate :class:`UnsatisfiedAssumption` (raised by
        :func:`ccai.testbase.properties.assume`) into
        :class:`pytest.skip` so an assumption-rejected example is
        reported as a skip rather than an error.

        Re-raises any other exception unchanged so genuine failures
        and errors keep their normal pytest semantics.

        :param item: The pytest ``Item`` whose call phase is being
                     run.

        :raises pytest.skip.Exception: When the test raises
                                       ``UnsatisfiedAssumption``.
    """
    try:
        item.runtest()
    except UnsatisfiedAssumption as ex:
        pytest.skip("UnsatisfiedAssumption: {}".format(ex))
    return
