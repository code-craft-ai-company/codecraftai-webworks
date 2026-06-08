# Project Structure

```
├── .kiro/                    # Kiro configuration and steering
├── .venv/                    # Virtual environment (do not modify)
├── development/              # Developer setup scripts
│   ├── setup-environment     # Creates virtual environment
│   └── setup-agent-container # Container setup
├── repository-setup/         # Repository initialization
│   ├── rehome-repository     # Creates .env file
│   └── repository-config.ini # Repository configuration
├── source/
│   ├── packages/             # Python package source
│   │   └── ccai/
│   │       └── webworks/
│   │           ├── asgi/     # ASGI application layer
│   │           ├── wsgi/     # WSGI application layer
│   │           └── persona/  # Web application persona
│   └── testroots/            # Test packages
│       └── ccai/
│           └── tests/
│               └── singlehost/
│                   └── webworks/  # Tests mirror source structure
├── specs/                    # Feature specifications
├── userguide/                # Standards and conventions docs
└── workspaces/               # VSCode workspace templates
```

## Key Conventions

### Test File Placement
Tests must mirror the source hierarchy:
- Source: `source/packages/ccai/webworks/asgi/application.py`
- Test: `source/testroots/ccai/tests/singlehost/webworks/asgi/test_application.py`

### Namespace Package
`source/packages/ccai` is a namespace package (no `__init__.py`). The first `__init__.py` appears at the package level (e.g., `webworks/__init__.py`).
