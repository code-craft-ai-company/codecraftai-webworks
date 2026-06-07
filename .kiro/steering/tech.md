# Tech Stack

## Language & Runtime
- Python 3.10+

## Build System
- Poetry for dependency management and packaging
- pyproject.toml for project configuration

## Dependencies
- requests
- codecraftai-this-app (application persona/identity)
- codecraftai-testbase (testing framework)
- codecraftai-configuration (config management)
- codecraftai-credentials (credential handling)
- codecraftai-dataprofiles (data profiles)

## Testing Framework
- testbase (custom framework, NOT pytest/unittest/hypothesis)
- Tests use `test_` prefix functions, not classes
- Mocking via `ccai.testbase.mocking` module

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

testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output
```

### Running Python in Virtual Environment
```bash
./python-env <args>
```

## Test Results
- Summary: `.output/testrun_summary.json`
- Detailed stream: `.output/testrun_results_stream.jsos`
