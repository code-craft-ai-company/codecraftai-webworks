# Tech Stack

## Language & Runtime
- Python 3.10+

## Build System
- Poetry for dependency management and packaging
- pyproject.toml for project configuration

## Dependencies
- requests
- automojo-this-app (application persona/identity)
- automojo-testbase (testing framework)
- automojo-configuration (config management)
- automojo-credentials (credential handling)
- automojo-dataprofiles (data profiles)

## Testing Framework
- testbase (custom framework, NOT pytest/unittest/hypothesis)
- Tests use `test_` prefix functions, not classes
- Mocking via `automojo.testbase.mocking` module

## Common Commands

### Environment Setup
```bash
# Initial setup (creates .env file)
./repository-setup/rehome-repository

# Create virtual environment
./development/setup-environment
```

### Running Tests
```bash
source .venv/bin/activate

testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost --output=./.output
```

### Running Python in Virtual Environment
```bash
./python-env <args>
```

## Test Results
- Summary: `.output/testrun_summary.json`
- Detailed stream: `.output/testrun_results_stream.jsos`
