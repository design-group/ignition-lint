# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install dependencies with Poetry
poetry install

# Note: --with dev is available for future dev-specific dependencies
# poetry install --with dev

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
# Run pylint on source code (uses .pylintrc configuration)
poetry run pylint ignition_lint/

# Format code with yapf (uses .style.yapf configuration)
poetry run yapf -ir ignition_lint/

# Check formatting without modifying files
poetry run yapf -dr ignition_lint/
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
Rules extend `LintingRule` and use the visitor pattern with automatic registration:

```python
from .common import LintingRule
from .registry import register_rule
from ..model.node_types import NodeType

@register_rule
class MyRule(LintingRule):
    def __init__(self, **kwargs):
        super().__init__({NodeType.COMPONENT})
    
    @property
    def error_message(self) -> str:
        return "Description of what this rule checks"
    
    def visit_component(self, component):
        # Rule logic here
        if some_condition:
            self.errors.append(f"{component.path}: Error message")
```

### Dynamic Rule Registration System
The framework now includes a comprehensive rule registration system that enables developers to create custom rules without modifying core framework files:

- **Automatic Discovery**: Rules are automatically discovered and registered when placed in `src/ignition_lint/rules/`
- **@register_rule Decorator**: Simple decorator-based registration for new rules
- **Configuration Preprocessing**: Rules can preprocess their configuration for type conversion and validation
- **Rule Validation**: Comprehensive validation ensures rules meet framework requirements
- **API Access**: Programmatic access to registered rules via registry API

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

📚 **[Complete Documentation Index](docs/README.md)** - Organized guide to all documentation

**Quick Access:**
- **New Developer?** → [Tutorial: Creating Your First Rule](docs/tutorial-creating-your-first-rule.md) 
- **Need Reference?** → [Developer Guide](docs/developer-guide-rule-creation.md)
- **API Questions?** → [API Reference](docs/api-reference-rule-registration.md)
- **Having Issues?** → [Troubleshooting Guide](docs/troubleshooting-rule-development.md)

**Additional Resources:**
- **Example Rules**: `src/ignition_lint/rules/example_rule.py` - Working examples
- **Rule Registry API**: Automatic discovery, validation, and registration system
- **Testing Framework**: Built-in test utilities for rule validation

Rules process specific node types and can access full view context through the flattened JSON representation.

## Python Style Guide

This project follows a customized version of Python's PEP 8 style guide with specific formatting rules enforced by yapf and pylint.

### Code Formatting

**Indentation:**
- Use **tabs instead of spaces** for indentation
- Tab width: 8 characters (configured in `.style.yapf`)
- Continuation lines: 4 spaces for alignment

**Line Length:**
- Maximum line length: **120 characters** (vs PEP 8's 79)
- Configured in both `.style.yapf` and `.pylintrc`

**Example:**
```python
# ✅ Correct - tabs for indentation
def process_component(self, component: ViewNode):
	"""Process a component node."""
	if component.name.startswith('temp'):
		self.errors.append(
			f"{component.path}: Component name '{component.name}' "
			f"should not use temporary naming"
		)
```

### Naming Conventions

Following PEP 8 and enforced by `.pylintrc`:

- **Functions and variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_CASE`
- **Private/internal:** `_leading_underscore`

```python
# ✅ Correct naming
class ComponentNameRule(LintingRule):
	MAX_NAME_LENGTH = 50
	
	def __init__(self):
		self.error_count = 0
		self._processed_components = []
```

### Docstrings and Comments

- Use triple quotes for docstrings
- Follow Google-style docstrings (configured in `.style.yapf`)
- Minimum docstring length: 10 characters (`.pylintrc`)

```python
def validate_component_name(self, name: str) -> bool:
	"""
	Validate that a component name follows naming conventions.
	
	Args:
		name: The component name to validate
		
	Returns:
		True if valid, False otherwise
	"""
	return len(name) >= 3 and name.isalnum()
```

### Import Organization

```python
# Standard library imports
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Third-party imports
import requests

# Local application imports
from .common import LintingRule
from .registry import register_rule
from ..model.node_types import ViewNode, NodeType
```

### Error Handling

- Use specific exceptions instead of generic `Exception`
- Follow the patterns established in `cli.py`:

```python
# ✅ Correct - specific exceptions
try:
	rule_instance = rule_class.create_from_config(kwargs)
except (TypeError, ValueError, AttributeError) as e:
	print(f"Error creating rule {rule_name}: {e}")

# ✅ Correct - file operations
try:
	json_data = read_json_file(file_path)
except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError) as e:
	print(f"Error reading file {file_path}: {e}")
```

### Type Hints

- Use type hints for function parameters and return values
- Import types from `typing` module when needed

```python
from typing import List, Dict, Optional, Set, Any

def create_rules_from_config(config: Dict[str, Any]) -> List[LintingRule]:
	"""Create rule instances from configuration."""
	rules: List[LintingRule] = []
	# Implementation here
	return rules
```

### YAPF Configuration Summary

Based on `.style.yapf`, the project uses:

- **Base style:** Google Python Style Guide
- **Column limit:** 120 characters
- **Indentation:** Tabs with 8-character width
- **Continuation indent:** 4 spaces
- **Bracket handling:** Coalesce and dedent closing brackets
- **Argument splitting:** When comma-terminated

### Formatting Commands

```bash
# Format all code with yapf
poetry run yapf -ir src/ tests/

# Check formatting without changes
poetry run yapf -dr src/ tests/

# Format specific file
poetry run yapf -i src/ignition_lint/cli.py
```

### Pre-commit Hooks

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

### Style Validation

```bash
# Check pylint compliance
poetry run pylint ignition_lint/

# Check yapf formatting
poetry run yapf -dr ignition_lint/
```

This style guide ensures consistent, readable code across the project while maintaining compatibility with the existing codebase and automated formatting tools.