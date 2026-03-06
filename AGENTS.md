# Personality
AI Agents working in this repository should refer to themselves as an agent named 'AutomationX'.

# Rules
- Look in the '<repository>/specs' folder for specification files that help to steer development work
- Look in the '<repository>/userguide' folder for files containing standards and conventions
- Look in the '<repository>/prompts' folder for pre-build prompts
- Files inside the .venv folder should not be modified, they are modified by the setup scripts
- Do not use hypothesis, unittest or pytest test frameworks.  Use only the testbase
- Place test results inside the .output folder, don't create .output-* directories in the root of the repository

# Project Overview

# Testing Conventions
The 'automojo-webworks' package repository utilizes the 'testbase' framework in order to run tests.  The 'testbase' test framework is used for single host testing or tests where only the machine running the tests is required.

Test are organized at the lowest level by resource configuration.  For example, all the single host tests for this package are in the folder 'source/testroots/automojo/tests/singlehost/webworks'.

AI based testing should run only the 'singlehost' tests tests with:

```
    source .venv/bin/activate
    
    testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost --output=./.output/
```

When running tests you should create an output folder in order to be able to capture all the test run artifacts in an isolated folder.


# Code Naming Conventions
The code naming conventions of this repository follows the [Naming Conventions](userguide/10-02-naming-conventions.rst) document.


# Code Structure
The code structure of this repository follows the [Code Organization](userguide/10-01-code-organization.rst) document

Remember to make the test hierarchy match the source hierarchy when adding test files.  For example:

File to test: 'source/packages/automojo/interop/protocols/dns/dnsquestion.py'
Test file location: 'source/testroots/automojo/interop/protocols/dns/test_dnsquestion.py'

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

The test tree should only contain resource origination declarations and tests.  It should not contain factories unless the usage of the factory is very isolated.  It is preferable to place factories in a folder such as a factory that creates the AutomationPodSimple object might be located at 'source/testroots/automojo/testshared/factories/automationpods/automationpodsimple.py'

# Using TestBase Mocking

The testbase framework provides its own mocking module that should be used instead of `unittest.mock`. Import the mocking utilities from `automojo.testbase.mocking`.

## Basic Mock Usage

```python
from automojo.testbase.mocking import Mock

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
from automojo.testbase.mocking import Mock

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
from automojo.testbase.mocking import create_module_patch, create_class_patch, create_instance_patch

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
    "name": "automojo.tests.singlehost.interop.protocols.dns.test_dnsaddress#test_write_passes_address",
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
    "name": "automojo.tests.singlehost.interop.protocols.dns.test_dnsaddress#test_write_passes_address",
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
