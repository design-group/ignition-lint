# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install dependencies with Poetry
poetry install

# Install with dev dependencies for development work
poetry install --with dev

# Activate virtual environment
poetry shell
```

### Testing
```bash
# Run all tests via test runner
cd tests
python test_runner.py --run-all

# Run only unit tests (fastest)
python test_runner.py --run-unit

# Run only integration tests
python test_runner.py --run-integration

# Run configuration-driven tests
python test_runner.py --run-config

# Run specific test file
python test_runner.py --test component_naming

# Set up test environment (creates directories, sample configs)
python test_runner.py --setup

# Alternative: Run tests via unittest discovery
python -m unittest discover tests
```

### Local GitHub Actions Testing
```bash
# Test all workflows before committing (prevents CI failures)
./test-actions.sh

# Test specific workflow
./test-actions.sh ci               # Run CI pipeline locally
./test-actions.sh unittest         # Run unit tests in CI environment  

# List available workflows
./test-actions.sh list

# Validate local testing setup
./validate-local-actions.sh

# Test with specific event (push, pull_request, etc.)
./test-actions.sh unittest pull_request
```

### Linting and Code Quality
```bash
# Run pylint on source code
poetry run pylint ignition_lint/

# Format code with black
poetry run black ignition_lint/
```

### Running the Tool
```bash
# Run on a specific file
poetry run python -m ignition_lint.main path/to/view.json

# Run with glob patterns
poetry run python -m ignition_lint.main --files "**/view.json"

# Run with custom configuration
poetry run python -m ignition_lint.main --config my_rules.json --files "views/**/view.json"

# CLI entry point (after poetry install)
ignition-lint --config rule_config.json --files "**/view.json"
```

## Architecture Overview

### Core Framework
Ignition Lint is a Python framework for analyzing Ignition Perspective view.json files using an object model approach with the visitor pattern.

**Key architectural components:**
- **JSON Flattening** (`common/flatten_json.py`): Converts hierarchical JSON to path-value pairs
- **Object Model** (`model/`): Builds structured representations from flattened JSON
- **Visitor Pattern Rules** (`rules/`): Extensible linting rules using visitor pattern
- **Lint Engine** (`linter.py`): Orchestrates model building and rule execution

### Directory Structure
```
src/ignition_lint/
├── cli.py              # Command-line interface
├── __main__.py         # Module entry point
├── linter.py          # Main linting engine
├── common/
│   └── flatten_json.py # JSON flattening utilities
├── model/
│   ├── builder.py     # ViewModelBuilder - constructs object model
│   └── node_types.py  # Node type definitions (Component, Binding, Script, etc.)
└── rules/
    ├── common.py      # Base LintingRule class
    ├── name_pattern.py # Component naming rules
    ├── polling_interval.py # Polling interval validation
    └── lint_script.py # Script quality rules via pylint
```

### Object Model Node Types
- **Component**: UI components with properties and metadata
- **ExpressionBinding**: Expression-based bindings
- **PropertyBinding**: Property-to-property bindings  
- **TagBinding**: Tag-based bindings
- **MessageHandlerScript**: Message handler scripts
- **CustomMethodScript**: Custom component methods
- **TransformScript**: Script transforms in bindings
- **EventHandlerScript**: Event handler scripts

### Rule Development Pattern
Rules extend `LintingRule` and use the visitor pattern:

```python
from .common import LintingRule
from ..model.node_types import NodeType

class MyRule(LintingRule):
    def __init__(self, **kwargs):
        super().__init__({NodeType.COMPONENT})
    
    def visit_component(self, component):
        # Rule logic here
        if some_condition:
            self.errors.append(f"{component.path}: Error message")
```

## Test-Driven Development

This codebase follows TDD principles:

1. **Write failing test first** in `tests/unit/` or `tests/integration/`
2. **Implement minimal code** to pass the test
3. **Refactor** while keeping tests green
4. **Add edge cases** and comprehensive test coverage

### Test Organization
- `tests/unit/`: One file per rule, fast isolated tests
- `tests/integration/`: Multi-component and CLI integration tests
- `tests/fixtures/`: Shared test utilities and base classes
- `tests/cases/`: Sample view.json files for testing
- `tests/configs/`: JSON configuration files for config-driven tests

### Key Test Utilities
- `BaseRuleTest`: Base class for rule unit tests
- `get_test_config()`: Helper for creating rule configurations
- `create_mock_view()`: Generate test view.json content
- `load_test_view()`: Load test cases from `tests/cases/`

## Configuration System

Rules are configured via JSON files (default: `rule_config.json`):

```json
{
  "ComponentNameRule": {
    "enabled": true,
    "kwargs": {
      "convention": "PascalCase",
      "allow_acronyms": true
    }
  },
  "PollingIntervalRule": {
    "enabled": true,
    "kwargs": {
      "minimum_interval": 10000
    }
  }
}
```

## Adding New Rules

The framework supports **extensible rule registration** - developers can add new rules without modifying core files:

### Quick Rule Creation
1. Create rule file in `src/ignition_lint/rules/my_rule.py`
2. Use the `@register_rule` decorator or inherit from `LintingRule`
3. Rules are automatically discovered and registered
4. Add to configuration JSON and use immediately

### Example
```python
from .common import LintingRule
from .registry import register_rule
from ..model.node_types import NodeType

@register_rule
class MyCustomRule(LintingRule):
    def __init__(self):
        super().__init__({NodeType.COMPONENT})
    
    @property
    def error_message(self) -> str:
        return "Custom rule description"
    
    def visit_component(self, component):
        # Rule logic here
        pass
```

### Developer Resources
- **Comprehensive Guide**: `docs/developer-guide-rule-creation.md`
- **Example Rules**: `src/ignition_lint/rules/example_rule.py`
- **Rule Registry API**: Automatic discovery, validation, and registration
- **Testing Framework**: Built-in test utilities for rule validation

Rules process specific node types and can access full view context through the flattened JSON representation.