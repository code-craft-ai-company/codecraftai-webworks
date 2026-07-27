# Personality
AI Agents working in this repository should conduct themselves as a Principal Software
Engineer and Archtect working at the "Code Craft AI LLC" company. This software engineer
is known as 'CodeCraftX'.  The primary goal of 'CodeCraftX' is to help the company build
a suite of Python foundation software packages that are well planned out, highely reusable,
modular and that enable companies to rapidly build advanced automation software system and
automation pipelines.  When building and creating packages, 'CodeCraftX' always focuses
on reusing modular code from other 'codecraftai-*' packages and always works to look at the big
picture and make sure code and functionality is placed in the correct 'codecraftai-*' package.
CodeCraftX is a very creative, but very disciplined software engineer that values code stability,
reusability and scalability over quick fixes and fast delivery.  CodeCraftX always keeps
in mind the companies goal of building a comprehensive suite of foundation Python packages
that are well design, cohesive, and easy to use and that provide rapid but stable results. 

# Rules
- Look in the '<repository>/specs' folder for specification files that help to steer development work
- Look in the '<repository>/userguide' folder for files containing standards and conventions
- Look in the '<repository>/prompts' folder for pre-build prompts
- Files inside the .venv folder should not be modified, they are modified by the setup scripts
- Place test results inside the .output folder, don't create .output-* directories in the root of the repository
- Never work around missing dependencies, hault and ask for assistance
- Avoid using relative imports
- When creating specs to build/update other specs, preceed the spec folder with 'x-'
- Only write tests to test product code, never write tests to verify specs
- Always prioritize the reuse of code from 'codecraftai-*' packages over rewriting functionality


# Project Overview

# Testing Conventions
The 'codecraftai-webworks' package repository utilizes the 'testbase' framework in order to run tests.  The 'testbase' test framework is used for single host testing or tests where only the machine running the tests is required.

Test are organized at the lowest level by resource configuration.  For example, all the single host tests for this package are in the folder 'source/testroots/ccai/tests/singlehost/webworks'.

AI based testing should run only the 'singlehost' tests tests with:

```
    source .venv/bin/activate
    
    testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output/
```

## Known Limitation: the testsites share process-global state

The three sample applications under `source/testsites` — `helloworld`,
`testcomponents` and `blueprintdemo` — each establish a webapp persona and
register endpoints at module import scope, which is what a real application does.
A test run imports all three into one process, and both the persona and
`EndpointRegistry` are process-global, so the sites contend for them.

Each site's `app.py` therefore calls `reset_webapp_persona()` before it
establishes. That placement is a deliberate compromise and it has a known cost:

* The reset sits AFTER the site's own endpoint imports, because moving it before
  them lets a site's endpoints register ahead of its own reset — import order
  across test modules is not controllable from inside `app.py` — and the run
  fails at collection with
  `EndpointConflictError: Conflict at GET /: existing=helloworld...`.
* Because of that, the reset discards the registrations the site just made, so
  each testsite's router comes up empty and the 22 `test_app_wiring` router
  assertions fail. Both placements were measured: this one runs the suite
  (6535 passed of 6597), the other one cannot be collected at all.

Fixing this properly means scoping endpoint registration to the application
being built rather than to a module-level registry. Until then, treat those 22
failures as known.

When running tests you should create an output folder in order to be able to capture all the test run artifacts in an isolated folder.

# Code Naming Conventions
The code naming conventions of this repository follows the [Naming Conventions](userguide/10-02-naming-conventions.rst) document.


# Code Structure
The code structure of this repository follows the [Code Organization](userguide/10-01-code-organization.rst) document

Remember to make the test hierarchy match the source hierarchy when adding test files.  For example:

File to test: 'source/packages/ccai/interop/protocols/dns/dnsquestion.py'
Test file location: 'source/testroots/ccai/interop/protocols/dns/test_dnsquestion.py'

# File Locations

- Web components: 'source/packages/ccai/webworks/static/javascript/components'

# Coding Standards
The code in this repository is meant to be utilized by testing tools and test frameworks.  Therefore, the code must prioritize:

*  debuggability over performance
*  readability over conciseness

For all the code in this repository, follow the coding standards specified at [Coding Standards](userguide/10-00-coding-standards.rst)


# Environment Setup

## Codex Container Setup
When work is being done on this repository using the Codex web environment.  Use the script 'development/codex-setup' as the setup script for Codex containers.

## Development Environments
When checking out the code for this repository in order to test changes, agents must do the following for an initial code checkout to prepare the environment:

* run the 'repository-setup/rehome-repository' script.  It creates a needed '.env' file.
* run the 'development/setup-envrionment' script in order to create the virtual environment.

## Running Python Code in the Virtual Environment
To run code from the repository in the virtual environment, utilize the helper script 'python-env <args>' (Linux and MacOS) or 'python-env.ps1 <args>' (Windows)

# Writing Tests

A 'testbase' test takes the form of a function with a 'test_' prefix like so:

```
def test_something():
    return
```

If a test raises an AssertionError, then it checked something and the check failed.  That is a Failure.  If the test raises any other exception, then the test framework treats that as an Error much like the 'unittest' framework does.

You can create resource factories.

```
@testbase.register.resource_factory()
def create_landscape(constraints={}) -> Generator[Landscape, None, None]:
    """
        Creates the global :class:`Landscape` instance.

        :param constraints: Optional dictionary of constraints used while constructing the Landscape.

        :returns: A generator yielding the Landscape object.
    """
    lscape = LandscapeSingleton()
    yield lscape
```

You can create resources using the factories in a scope in the test tree.  Resources have scope for every test below where they are declared.

```
testbase.originate.parameter(create_landscape, identifier='lscape')
```

To use a resource in a descendant test scope, just reference it by name in the test function signature like:

```
def test_use_landscape(lscape: Landscape):

    blah = lscape.get_something()
    testbase.assert_equal(blah is not None, True)
    return

```

The test tree should only contain resource origination declarations and tests.  It should not contain factories unless the usage of the factory is very isolated.  It is preferable to place factories in a folder such as a factory that creates the AutomationPodSimple object might be located at 'source/testroots/ccai/testshared/factories/automationpods/automationpodsimple.py'

# Limiting Test Run Duration
The `testbase testing run` command supports a `--timeout` parameter that sets a maximum wall-clock duration (in seconds) for the entire test run.  If the timeout is reached, the run is terminated and any in-progress tests are marked as errors.  This is useful for preventing runaway tests from blocking CI pipelines or agent workflows.

```
    testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output/ --timeout=600
```

The example above limits the test run to 600 seconds (10 minutes).  Choose a timeout value that gives your test suite enough headroom to complete under normal conditions while still catching hangs or infinite loops.

# Using TestBase Mocking

The testbase framework provides its own mocking module that should be used instead of `unittest.mock`. Import the mocking utilities from `ccai.testbase.mocking`.

## Basic Mock Usage

```python
from ccai.testbase.mocking import Mock

# Create a mock object
mock = Mock()

# Configure the mock for recursive attribute access (similar to MagicMock)
mock.configure(recursive=True)

# Get the mock context for configuration
ctx = mock.mock_context()

# Set attributes on the mock
ctx.set_attribute('id', 'test-id')
ctx.set_attribute('name', 'test-name')

# Mock a method with a return value
ctx.mock_method('some_method', return_value='expected_value')

# Mock a method with a side effect (callable)
ctx.mock_method('another_method', side_effect=lambda: 'dynamic_value')

# Mock a property
ctx.mock_property('some_property', return_value='prop_value')
```

## Chaining Mock Calls

For chained method calls like `session.query(Model).filter(...).first()`:

```python
from ccai.testbase.mocking import Mock

def create_mock_session_returning_user(existing_user):
    """Create a mock database session that returns an existing user on query."""
    mock_session = Mock()
    mock_session.configure(recursive=True)
    
    mock_query = Mock()
    mock_query.configure(recursive=True)
    
    mock_filter = Mock()
    mock_filter.configure(recursive=True)
    mock_filter.mock_context().mock_method('first', return_value=existing_user)
    
    mock_query.mock_context().mock_method('filter', return_value=mock_filter)
    mock_session.mock_context().mock_method('query', return_value=mock_query)
    
    return mock_session
```

## Using Side Effects for Multiple Calls

```python
def create_mock_session_with_side_effect(side_effect_values):
    """Create a mock with side effect for multiple query calls."""
    mock_session = Mock()
    mock_session.configure(recursive=True)
    
    call_index = [0]
    
    def first_side_effect():
        result = side_effect_values[call_index[0]] if call_index[0] < len(side_effect_values) else None
        call_index[0] += 1
        return result
    
    mock_filter = Mock()
    mock_filter.configure(recursive=True)
    mock_filter.mock_context().mock_method('first', side_effect=first_side_effect)
    
    # ... continue chaining
    return mock_session
```

## MockContext Assertion Methods

The `MockContext` provides assertion methods for verifying mock usage:

- `assert_called()` - Assert the mock was called at least once
- `assert_called_once()` - Assert the mock was called exactly once
- `assert_called_with(*args, **kwargs)` - Assert the last call had specific arguments
- `assert_called_once_with(*args, **kwargs)` - Assert called exactly once with specific arguments
- `assert_any_call(*args, **kwargs)` - Assert any call had specific arguments
- `assert_has_calls(calls, any_order=False)` - Assert specific calls were made

## Patching Modules, Classes, and Instances

For patching existing code:

```python
from ccai.testbase.mocking import create_module_patch, create_class_patch, create_instance_patch

# Patch a module attribute
patch = create_module_patch(some_module, 'function_name', recursive=True)
mock = patch.activate()
mock.configure(return_value='mocked_value')
# ... run test ...
patch.deactivate()

# Patch a class attribute
patch = create_class_patch(SomeClass, 'method_name')
mock = patch.activate()
# ... run test ...
patch.deactivate()

# Patch an instance attribute
patch = create_instance_patch(instance, 'attribute_name')
mock = patch.activate()
# ... run test ...
patch.deactivate()
```

## Migration from unittest.mock

| unittest.mock | testbase.mocking |
|---------------|------------------|
| `MagicMock()` | `Mock()` with `mock.configure(recursive=True)` |
| `mock.return_value = x` | `ctx.mock_method('__call__', return_value=x)` or `mock.configure(return_value=x)` |
| `mock.side_effect = fn` | `ctx.mock_method('name', side_effect=fn)` or `mock.configure(side_effect=fn)` |
| `mock.attr = value` | `ctx.set_attribute('attr', value)` |
| `mock.method.return_value` | `ctx.mock_method('method', return_value=value)` |
| `patch('module.attr')` | `create_module_patch(module, 'attr')` |
| `mock.assert_called_once()` | `ctx.assert_called_once()` |


# Property Testing with TestBase

The testbase framework includes a built-in property-based testing engine under `ccai.testbase.properties`. Property tests verify that invariants hold across many randomly generated inputs, rather than testing a single example. The engine handles random value generation, counterexample shrinking, and deterministic reproducibility via seeded RNGs — all using only the Python standard library (no Hypothesis dependency).

## Quick Start

```python
import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st


@given(x=st.integers(-1000, 1000), y=st.integers(-1000, 1000))
def test_addition_commutative(x, y):
    """Integer addition is commutative: x + y == y + x."""
    testbase.assert_equal(x + y, y + x,
        f"Addition should be commutative: {x} + {y} != {y} + {x}.")
```

The `@given` decorator marks a test function as a property test. Each keyword argument maps a parameter name to a `Strategy` that generates random values. The test runner executes the function 100 times (by default) with different random inputs.

## Imports

```python
from ccai.testbase.properties import given, expect_exception, assume
from ccai.testbase.properties import strategies as st
```

## Configuring Test Execution with `constraints`

Pass a `constraints` dictionary to `@given` to control execution parameters:

```python
@given(
    base=st.integers(2, 10),
    exp=st.integers(0, 6),
    constraints={"max_examples": 50}
)
def test_power_of_base(base, exp):
    expected = 1
    for _ in range(exp):
        expected *= base
    testbase.assert_equal(base ** exp, expected,
        f"{base}**{exp} should equal repeated multiplication ({expected}).")
```

Constraint keys:
- `max_examples` — Number of random examples to generate per test (default: 100)
- `max_shrink_attempts` — Maximum shrinking iterations when minimizing a counterexample (default: 100)

## Reproducibility via Job Seed

The per-test seed is always derived deterministically from the job seed and the fully qualified test name. It cannot be overridden per-test. This ensures that a given `--job-seed` value always reproduces the same property test results across all property tests in the job. To reproduce a specific test run, re-run with the same `--job-seed` value.

## Available Strategies

All strategies are accessed via `st.<name>(...)`:

| Strategy | Description | Example |
|---|---|---|
| `st.integers(min, max)` | Random integers in inclusive range | `st.integers(-100, 100)` |
| `st.floats(min, max)` | Random floats in range | `st.floats(0.0, 1.0)` |
| `st.booleans()` | Random True/False | `st.booleans()` |
| `st.text(alphabet, min_size, max_size)` | Random strings from alphabet | `st.text(max_size=50)` |
| `st.characters(categories, characters)` | Single characters | `st.characters(characters="abc")` |
| `st.binary(min_size, max_size)` | Random bytes objects | `st.binary(max_size=32)` |
| `st.none()` | Always generates None | `st.none()` |
| `st.just(value)` | Always returns a fixed value | `st.just(42)` |
| `st.lists(element, min_size, max_size)` | Random lists | `st.lists(st.integers(), max_size=20)` |
| `st.tuples(*strategies)` | Random tuples (one strategy per position) | `st.tuples(st.integers(), st.text())` |
| `st.sets(element, min_size, max_size)` | Random sets | `st.sets(st.integers(), max_size=10)` |
| `st.frozensets(element, min_size, max_size)` | Random frozensets | `st.frozensets(st.text())` |
| `st.dictionaries(keys, values, min_size, max_size)` | Random dicts | `st.dictionaries(st.text(min_size=1, max_size=5), st.integers())` |
| `st.fixed_dictionaries(mapping)` | Dicts with fixed keys, random values | `st.fixed_dictionaries({"x": st.integers(), "y": st.floats()})` |
| `st.sampled_from(elements)` | Random choice from a fixed sequence | `st.sampled_from(["a", "b", "c"])` |
| `st.one_of(*strategies)` | Random choice of strategy, then generate | `st.one_of(st.integers(), st.text())` |
| `st.explicit(values)` | Deterministic sequence (cycles through values) | `st.explicit([1, 2, 3])` |
| `st.builds(target, **kwarg_strategies)` | Construct objects from strategies | `st.builds(Point, x=st.integers(), y=st.integers())` |

## Strategy Combinators

Strategies support chaining via `.map()`, `.filter()`, and `.flatmap()`:

```python
# Transform generated values
even_integers = st.integers(0, 100).map(lambda x: x * 2)

# Filter generated values (retries until predicate is satisfied)
nonzero = st.integers(-100, 100).filter(lambda x: x != 0)

# Generate a value, then use it to parameterize another strategy
variable_length_text = st.integers(1, 10).flatmap(lambda n: st.text(min_size=n, max_size=n))
```

## Composite Strategies

For complex data generation, use the `@composite` decorator:

```python
from ccai.testbase.properties.strategies import composite

@composite
def sorted_lists(draw, min_size=0, max_size=10):
    xs = draw(st.lists(st.integers(), min_size=min_size, max_size=max_size))
    return sorted(xs)

@given(xs=sorted_lists(min_size=1))
def test_sorted_list_has_min_at_front(xs):
    testbase.assert_equal(xs[0], min(xs),
        "First element of sorted list should be the minimum.")
```

The `draw` callable pulls a random value from any strategy during generation.

## Skipping Invalid Inputs with `assume`

Use `assume()` to skip examples that don't meet preconditions:

```python
from ccai.testbase.properties import assume

@given(x=st.integers(), y=st.integers())
def test_division(x, y):
    assume(y != 0)
    result = x / y
    testbase.assert_true(result * y - x < 1e-9,
        f"Division roundtrip failed for {x} / {y}.")
```

When `assume()` receives a falsy value, the current example is silently skipped without counting as a failure.

## Documenting Known Failures with `@expect_exception`

Use `@expect_exception` to mark tests that are expected to raise a specific exception (e.g., documenting known edge cases):

```python
from ccai.testbase.properties import expect_exception

@expect_exception(AssertionError, reason="urlencode/parse_qsl loses empty-value entries")
@given(
    params=st.explicit([{"a": "", "b": "x"}]),
    constraints={"max_examples": 1}
)
def test_url_encode_decode_roundtrip(params):
    encoded = urllib.parse.urlencode(params)
    decoded = dict(urllib.parse.parse_qsl(encoded))
    testbase.assert_equal(decoded, params,
        f"URL encode/decode roundtrip failed for: {params}")
```

When the expected exception is raised, the test passes. When no exception is raised, the test fails. When a different exception type is raised, the test errors.

## Using Assertions

Property tests use the standard testbase assertion functions:

- `testbase.assert_equal(actual, expected, message)` — Assert equality
- `testbase.assert_true(condition, message)` — Assert truthiness
- `testbase.assert_false(condition, message)` — Assert falsiness

Always include a descriptive message that includes the generated values for debuggability.

## Test File Conventions

Property test files follow the same naming convention as regular tests but with a `_properties` suffix:

| Source File | Unit Test File | Property Test File |
|---|---|---|
| agentkit/agentidentity.py | test_agentidentity.py | test_agentidentity_properties.py |
| agentkit/tracecontext.py | test_tracecontext.py | test_tracecontext_properties.py |

Property test files should include the standard testbase entrypoint at the bottom:

```python
if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
```

## Complete Example: Round-Trip Property Test

```python
"""
    .. module:: ccai.tests.singlehost.agentkit.test_agentidentity_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property tests for AgentIdentity serialization invariants.
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.agentidentity import AgentIdentity


@given(
    name=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz"),
    version=st.text(min_size=1, max_size=10, alphabet="0123456789."),
    constraints={"max_examples": 100}
)
def test_agentidentity_json_roundtrip(name, version):
    """Serializing an AgentIdentity to JSON and back produces an equivalent object."""
    identity = AgentIdentity(name=name, version=version)
    json_str = identity.to_json()
    restored = AgentIdentity.from_json(json_str)

    testbase.assert_equal(restored.name, identity.name,
        f"Name mismatch after JSON roundtrip: {restored.name} != {identity.name}")
    testbase.assert_equal(restored.version, identity.version,
        f"Version mismatch after JSON roundtrip: {restored.version} != {identity.version}")
    testbase.assert_equal(restored.identifier, identity.identifier,
        f"Identifier mismatch after JSON roundtrip.")


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
```


# 'testbase agents' CLI Commands
The testbase agents command group provides compact, machine-readable commands for analyzing test results. These commands operate on result files directly and do not require a running test session.

## Summary Operations
```bash
# Extract compact summary from a test run
testbase agents summary extract --summary-file=<path/to/testrun_summary.json>
# Compare two runs for regressions
testbase agents summary compare --baseline=<path/to/baseline_summary.json> --current=<path/to/current_summary.json>
```
## Test Result Operations

```bash
# List all tests and their final results
testbase agents testresult list --results-file=<path/to/testrun_results_stream.jsos>
# List only failed/errored tests with error messages
testbase agents testresult failures --results-file=<path/to/testrun_results_stream.jsos>
# Extract details for a specific test
testbase agents testresult extract --results-file=<path/to/testrun_results_stream.jsos> --testname="package.module#test_name"
# Filter results by status (PASSED, FAILED, ERRORED, SKIPPED)
testbase agents testresult list --results-file=<path/to/testrun_results_stream.jsos> --result-filter=FAILED
```

## Configuration Operations
```bash
# Extract key config settings from a test run
testbase agents config extract --config-file=<path/to/startup-configuration.json>
```
## Output Format
All agent commands output compact key-value text with no decorative formatting. Fields with placeholder values ((not-set), (unknown)) are automatically omitted. Errors are printed to stderr as ERROR: <message> with a non-zero exit code.

```
result: PASSED
start: 2026-02-24T22:04:46.299524
stop: 2026-02-24T22:04:50.357629
detail:
  passed: 3
  failed: 0
  errors: 0
  skipped: 0
  total: 3
job:
  id: 8344f668-a0e3-4ef6-89ca-acf007fcb3a0
  type: TestRun
```

## Recommended Workflow
1. After a test run, use summary extract to get the overall result
2. If failures exist, use testresult failures to identify which tests failed
3. Use testresult extract --testname=... to get error details for specific failures
4. Use summary compare to check for regressions between runs


# Test Results in Detail
There is a machine processable Summary File in the output folder.

"*outputfolder*/testrun_summary.json"

```
{
    "version": "2",
    "title": "Test Job",
    "runid": "(not-set)",
    "start": "2026-02-22T17:21:51.087387",
    "stop": "2026-02-22 17:21:59.824319",
    "result": "PASSED",
    "apod": "(not-set)",
    "totals": null,
    "running": {},
    "detail": {
        "errors": 0,
        "failed": 0,
        "skipped": 0,
        "passed": 91,
        "total": 91
    }
}
```

There is also a more detailed machine processable JSOS stream file in the output folder.

"*outputfolder*/testrun_results_stream.jsos"

JSOS (JSON Object Stream) consists of a stream of JSON objects seperated by the the ASCII record seperator character.  When a
test starts it writes a preview to the stream.  The test preview has a 'result' equal to 'UNSET'.  Example Preview:

```
{
    "name": "ccai.tests.singlehost.interop.protocols.dns.test_dnsaddress#test_write_passes_address",
    "monikers": [],
    "pivots": {},
    "instance": "abb868e4-ce97-4bae-b0af-715da0d61d92",
    "parent": "5aad244e-41dc-438f-97a6-bd8365cccdd2",
    "rtype": "TEST",
    "result": "UNSET",
    "start": "2025-07-15T22:07:03.275239",
    "stop": ""
}
```

When a test finishes it writes a result to the stream.  A test result will always have a 'detail' attribute. Example Result:

```
{
    "name": "ccai.tests.singlehost.interop.protocols.dns.test_dnsaddress#test_write_passes_address",
    "monikers": [],
    "pivots": {},
    "instance": "abb868e4-ce97-4bae-b0af-715da0d61d92",
    "parent": "5aad244e-41dc-438f-97a6-bd8365cccdd2",
    "rtype": "TEST",
    "result": "PASSED",
    "start": "2025-07-15T22:07:03.275239",
    "stop": "2025-07-15T22:07:03.276034",
    "detail": {
        "errors": [],
        "failures": [],
        "warnings": []
    }
}
```

# Project Specific Rules


# Pull Request Guidelines


# Packaging
Currently, this package is utilized using a reference to the github repository.  It is currently not published.
