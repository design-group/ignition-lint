# Ignition Lint Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the ignition-lint codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents working on enhancements to this Python-based linting framework for Ignition Perspective view.json files.

### Document Scope

Comprehensive documentation of entire system architecture, focusing on the object model builder, visitor pattern implementation, and testing infrastructure.

### Change Log

| Date | Version | Description | Author |
| ---- | ------- | ----------- | ------ |
| 2025-08-23 | 1.0 | Initial brownfield analysis | Claude Code |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

- **Main Entry**: `src/ignition_lint/cli.py` - Command-line interface and argument parsing
- **Module Entry**: `src/ignition_lint/__main__.py` - Python module entry point
- **Core Engine**: `src/ignition_lint/linter.py` - Main linting orchestration
- **Object Model Builder**: `src/ignition_lint/model/builder.py` - Converts flattened JSON to node objects
- **Node Definitions**: `src/ignition_lint/model/node_types.py` - All node types and visitor pattern implementation
- **Base Rule Classes**: `src/ignition_lint/rules/common.py` - Abstract rule classes with visitor pattern
- **JSON Flattening**: `src/ignition_lint/common/flatten_json.py` - Hierarchical to path-value conversion
- **Configuration**: `rule_config.json` - Default rule configuration
- **GitHub Action**: `action.yml` - GitHub Actions composite action definition

### Key Algorithm Files

- **Component Naming**: `src/ignition_lint/rules/name_pattern.py` - Complex naming pattern validation with abbreviation handling
- **Script Linting**: `src/ignition_lint/rules/lint_script.py` - Pylint integration with batch processing
- **Polling Validation**: `src/ignition_lint/rules/polling_interval.py` - Expression parsing for now() intervals

## High Level Architecture

### Technical Summary

Ignition Lint is a sophisticated Python framework that analyzes Ignition Perspective view.json files using a three-stage pipeline:
1. **Flattening**: Converts hierarchical JSON to dot-notation paths
2. **Model Building**: Creates typed node objects from flattened data
3. **Rule Processing**: Applies visitor pattern rules to validate nodes

### Actual Tech Stack (from pyproject.toml)

| Category | Technology | Version | Notes |
| -------- | ---------- | ------- | ----- |
| Runtime | Python | >=3.9,<3.13 | Poetry managed |
| Linting | pylint | * | Used both internally and for script validation |
| Stubs | ignition-api-stubs | ^8.1.48.post1 | Ignition API type hints |
| Pre-commit | pre-commit | ^4.2.0 | Git hooks |
| Build System | poetry-core | >=1.0.0 | Poetry build backend |
| Package Manager | Poetry | 2.0+ | Dependency management |

### Repository Structure Reality Check

- Type: Single package repository
- Package Manager: Poetry with lock file
- CLI Tool: Installable via `poetry install` as `ignition-lint` command

## Source Tree and Module Organization

### Project Structure (Actual)

```text
ignition-lint/
├── src/ignition_lint/         # Main package
│   ├── cli.py                 # CLI interface with comprehensive arg parsing
│   ├── __main__.py            # Module entry point
│   ├── linter.py              # Core LintEngine orchestration
│   ├── common/
│   │   └── flatten_json.py    # JSON flattening utilities
│   ├── model/
│   │   ├── builder.py         # ViewModelBuilder - complex JSON parsing
│   │   └── node_types.py      # Node hierarchy with visitor pattern
│   └── rules/
│       ├── __init__.py        # RULES_MAP registry
│       ├── common.py          # Base rule classes with visitor pattern
│       ├── name_pattern.py    # Complex naming rule with abbreviations
│       ├── lint_script.py     # Pylint integration rule
│       └── polling_interval.py # Expression parsing rule
├── tests/                     # Comprehensive testing framework
│   ├── test_runner.py         # Custom test runner script
│   ├── conftest.py            # Pytest fixtures (NOTE: some tests use unittest)
│   ├── fixtures/              # Shared test infrastructure
│   │   ├── base_test.py       # BaseRuleTest and BaseIntegrationTest
│   │   └── config_framework.py # Configuration-driven testing
│   ├── unit/                  # Unit tests per rule
│   ├── integration/           # Multi-component tests
│   ├── cases/                 # Sample view.json files for testing
│   └── configs/               # JSON-driven test configurations
├── action.yml                 # GitHub Actions composite action
├── rule_config.json          # Default linting configuration
├── pyproject.toml            # Poetry configuration
└── _temp/                     # Temporary development files
```

### Key Modules and Their Purpose

- **CLI Layer**: `src/ignition_lint/cli.py` - Handles file discovery, rule creation, and output formatting
- **Linting Engine**: `src/ignition_lint/linter.py` - Orchestrates model building and rule execution
- **Object Model**: `src/ignition_lint/model/` - Converts JSON to structured node hierarchy
- **Rule System**: `src/ignition_lint/rules/` - Visitor pattern implementation for validation
- **Testing Framework**: `tests/` - Custom test runner with config-driven and traditional unit tests

## Data Models and APIs

### Data Models

Instead of duplicating, reference actual model files:

- **ViewNode Base Class**: See `src/ignition_lint/model/node_types.py:29-60`
- **Component Nodes**: See `src/ignition_lint/model/node_types.py:62-74`
- **Binding Nodes**: See `src/ignition_lint/model/node_types.py:76-109`
- **Script Nodes**: See `src/ignition_lint/model/node_types.py:112-194`
- **Property Nodes**: See `src/ignition_lint/model/node_types.py:197-207`

### Object Model Architecture

The system uses a sophisticated node type hierarchy:

```text
ViewNode (Abstract Base)
├── Component (UI components with properties)
├── ExpressionBinding (Expression-based bindings)
├── PropertyBinding (Property-to-property bindings)
├── TagBinding (Tag-based bindings)
├── ScriptNode (Abstract base for scripts)
│   ├── MessageHandlerScript (Message handlers with scope)
│   ├── CustomMethodScript (Custom methods with parameters)
│   ├── TransformScript (Binding transforms)
│   └── EventHandlerScript (Event handlers)
└── Property (Individual component properties)
```

### API Specifications

- **CLI Arguments**: See `src/ignition_lint/cli.py:175-214` for complete argument specification
- **Rule Configuration**: See `rule_config.json` for JSON schema
- **GitHub Action Inputs**: See `action.yml:5-24` for action interface

## Technical Debt and Known Issues

### Critical Technical Debt

1. **GitHub Action**: Action.yml references non-existent file `src/ignition_lint.py` (line 35), should be updated to use proper CLI entry point
2. **Testing Parameter Issues**: Test runner has some parameter passing problems mentioned in user requirements
3. **Inconsistent Test Frameworks**: Mix of unittest and pytest patterns in test suite
4. **GitHub Actions Incomplete**: Integration test workflow uses old action reference and incomplete setup

### Workarounds and Gotchas

- **Path Handling**: CLI uses glob patterns but filters specifically for `view.json` files (line 100 in cli.py)
- **Rule Registration**: Rules must be manually added to RULES_MAP in `src/ignition_lint/rules/__init__.py`
- **Script Processing**: PylintScriptRule creates temporary debug files in `debug/` directory for troubleshooting
- **Node Type Conversion**: NamePatternRule requires string-to-enum conversion in preprocess_config (lines 23-52)
- **Error Output**: Uses emoji and colored output which may not work in all environments

### Testing Framework Issues

- **Mixed Testing Approaches**: Uses both unittest (BaseRuleTest) and pytest (conftest.py) patterns
- **Parameter Passing**: Custom test_runner.py may not pass parameters correctly to some test configurations
- **Configuration Framework**: Complex config-driven testing system in `fixtures/config_framework.py`
- **Path Dependencies**: Tests rely on relative path discovery which can be brittle

## Integration Points and External Dependencies

### External Services

| Service | Purpose | Integration Type | Key Files |
| ------- | ------- | --------------- | --------- |
| Pylint | Script validation | Python import | `src/ignition_lint/rules/lint_script.py` |
| Ignition API | Type hints | Development dependency | pyproject.toml |

### Internal Integration Points

- **Poetry Integration**: Package installable as CLI tool via `poetry install`
- **GitHub Actions**: Composite action for CI/CD integration
- **Pre-commit**: Can be integrated as pre-commit hook
- **File System**: Creates debug files in `debug/` directory during script linting

## Development and Deployment

### Local Development Setup

1. **Install Dependencies**: `poetry install` (includes dev dependencies automatically)
2. **Activate Environment**: `poetry shell` or use `poetry run` prefix
3. **Run Tests**: `cd tests && python test_runner.py --run-all`
4. **Setup Test Environment**: `cd tests && python test_runner.py --setup`

### Build and Deployment Process

- **CLI Tool**: Install via `poetry install`, creates `ignition-lint` command
- **Run as Module**: `python -m ignition_lint` after adding src to path
- **GitHub Action**: Use composite action from repository
- **Package Build**: `poetry build` creates wheel and sdist

### Current Command Patterns

```bash
# Development usage
poetry run python -m ignition_lint --files "**/view.json"
poetry run python -m ignition_lint --config custom_rules.json

# After installation
ignition-lint --files "**/view.json" --verbose
ignition-lint --config rule_config.json --analyze-rules

# Testing
cd tests && python test_runner.py --run-unit --verbose
cd tests && python test_runner.py --test component_naming
```

## Testing Reality

### Current Test Coverage

- **Unit Tests**: Per-rule testing in `tests/unit/` directory
- **Integration Tests**: Multi-component testing in `tests/integration/`
- **Configuration Tests**: JSON-driven test cases in `tests/configs/`
- **Custom Test Runner**: `tests/test_runner.py` with discovery and filtering

### Test Framework Architecture

**CRITICAL ISSUE**: Mixed testing frameworks cause confusion
- **Unittest Pattern**: `BaseRuleTest` and `BaseIntegrationTest` classes
- **Pytest Pattern**: Fixtures in `conftest.py`
- **Custom Framework**: Configuration-driven testing via `config_framework.py`

### Running Tests

```bash
# Custom test runner (primary method)
cd tests
python test_runner.py --run-unit          # Unit tests only
python test_runner.py --run-integration   # Integration tests
python test_runner.py --run-config        # Config-driven tests
python test_runner.py --run-all           # All tests
python test_runner.py --test name_pattern # Specific test

# Alternative (unittest discovery)
python -m unittest discover tests

# Test setup
python test_runner.py --setup  # Creates directories and sample configs
```

## GitHub Actions Integration

### Current Action Definition

**CRITICAL ISSUE**: `action.yml` has broken file reference

```yaml
# BROKEN - references non-existent file
run: |
  python ${{ github.action_path }}/src/ignition_lint.py  # THIS FILE DOESN'T EXIST
```

Should reference proper entry point:
```yaml
run: |
  python ${{ github.action_path }}/src/ignition_lint/__main__.py
```

### GitHub Workflows

- **Unit Test Workflow**: `.github/workflows/unittest.yml` - Basic Python 3.12 testing
- **Integration Test Workflow**: `.github/workflows/integration-test.yml` - Tests action usage

### Action Usage Issues

**TECHNICAL DEBT**: The action workflows show usage but the action itself is incomplete
- Integration test references `ia-eknorr/ignition-lint@v2.1` (external repo)
- Local action.yml doesn't work due to file path issues
- Parameter mapping between action inputs and CLI arguments needs verification

## Core Architecture Deep Dive

### JSON Flattening Process

The system converts hierarchical JSON to dot-notation paths:

```python
# Original hierarchical structure
{
  "root": {
    "children": [{
      "meta": {"name": "Button1"},
      "props": {"text": "Click Me"}
    }]
  }
}

# Flattened to paths
{
  "root.children[0].meta.name": "Button1",
  "root.children[0].props.text": "Click Me"
}
```

### Object Model Building

`ViewModelBuilder` (`src/ignition_lint/model/builder.py`) parses flattened JSON through specialized collectors:
- `_collect_components()` - Finds meta.name entries
- `_collect_bindings()` - Parses binding.type configurations
- `_collect_message_handlers()` - Extracts messageHandlers scripts
- `_collect_custom_methods()` - Parses customMethods with parameters
- `_collect_event_handlers()` - Processes event scripts
- `_collect_properties()` - Captures remaining properties

### Visitor Pattern Implementation

Rules implement the visitor pattern via `LintingRule` base class:

```python
class MyRule(LintingRule):
    def __init__(self, target_node_types=None):
        super().__init__(target_node_types or {NodeType.COMPONENT})

    def visit_component(self, node):
        # Rule logic for components
        if some_validation_fails:
            self.errors.append(f"{node.path}: Error message")
```

### Rule Processing Pipeline

1. **Node Collection**: `LintEngine.process()` builds object model
2. **Rule Filtering**: Each rule gets nodes matching its `target_node_types`
3. **Visitor Dispatch**: Nodes call `node.accept(rule)` → `rule.visit_<type>(node)`
4. **Error Aggregation**: Rules accumulate errors in `self.errors`
5. **Batch Processing**: `ScriptRule` base class enables batch script processing

## Rule Implementation Patterns

### Naming Rule Complexity

`NamePatternRule` is the most sophisticated rule with:
- **Multiple Conventions**: PascalCase, camelCase, snake_case, kebab-case, etc.
- **Abbreviation Handling**: Common tech abbreviations (API, JSON, etc.)
- **Node-Specific Rules**: Different conventions per node type
- **Auto-Suggestions**: Provides naming suggestions in error messages

### Script Processing Architecture

`PylintScriptRule` implements batch processing:
- **Script Collection**: Collects all script nodes during visitor phase
- **Batch Processing**: Combines scripts into single file for pylint
- **Debug Support**: Saves temp files and pylint output for troubleshooting
- **Line Mapping**: Maps pylint errors back to original script locations

### Polling Interval Validation

`PollingIntervalRule` uses regex parsing to validate `now()` expressions:
- **Expression Analysis**: Parses `now(interval)` patterns
- **Minimum Validation**: Ensures intervals meet minimum threshold
- **Flexible Matching**: Handles various expression formats

## Configuration System Reality

### Rule Configuration Format

Rules are configured via JSON with preprocessing:

```json
{
  "NamePatternRule": {
    "enabled": true,
    "kwargs": {
      "target_node_types": ["component", "property"],
      "node_type_specific_rules": {
        "component": {
          "convention": "PascalCase",
          "min_length": 3
        }
      }
    }
  }
}
```

### Configuration Preprocessing

**CRITICAL PATTERN**: Rules can preprocess their configuration via `preprocess_config()` class method:
- **String to Enum**: Converts string node types to `NodeType` enums
- **Validation**: Validates configuration before rule instantiation
- **Default Handling**: Applies default values and transformations

### Rule Registry

Rules must be manually registered in `RULES_MAP`:
```python
RULES_MAP = {
    "PylintScriptRule": PylintScriptRule,
    "PollingIntervalRule": PollingIntervalRule,
    "NamePatternRule": NamePatternRule,
}
```

## Frequently Used Commands and Scripts

### Development Commands

```bash
# Setup
poetry install                              # Install dependencies
poetry install --with dev                   # Install with dev dependencies
poetry shell                               # Activate virtual environment

# Running the tool
poetry run python -m ignition_lint --files "**/view.json"
poetry run python -m ignition_lint --config rule_config.json --verbose
ignition-lint --files "views/**/view.json" # After poetry install

# Testing
cd tests && python test_runner.py --setup  # Setup test environment
cd tests && python test_runner.py --run-all # Run all tests
cd tests && python test_runner.py --test component_naming # Specific test

# Code quality
poetry run pylint ignition_lint/           # Lint source code
poetry run black ignition_lint/            # Format code

# Build and distribution
poetry build                               # Build package
poetry export --output requirements.txt    # Export dependencies
```

### Debugging and Troubleshooting

- **Debug Files**: Check `debug/` directory for pylint temp files and output
- **Verbose Mode**: Use `--verbose` for detailed statistics and analysis
- **Rule Analysis**: Use `--analyze-rules` to see which nodes rules will process
- **Test Debugging**: Use `--verbose` with test runner for detailed output

### Common Issues and Solutions

**"No files found"**:
- Check file patterns, system looks specifically for `view.json` files
- Use absolute paths or verify current directory

**"Unknown rule" errors**:
- Verify rule is registered in `RULES_MAP`
- Check rule class name matches configuration

**GitHub Action failures**:
- Action.yml needs to be fixed to reference correct entry point
- Parameter mapping may need verification

## Appendix - Advanced Architecture Notes

### Visitor Pattern Benefits

The visitor pattern enables:
- **Separation of Concerns**: Node structure separate from validation logic
- **Easy Extensibility**: Add new rules without modifying node classes
- **Type Safety**: Each node type has specific visit method
- **Flexible Processing**: Rules choose which nodes to process

### Object Model Design Decisions

- **Immutable Nodes**: Nodes represent parsed state, not modified during linting
- **Path Preservation**: All nodes maintain full JSON path for error reporting
- **Type Hierarchy**: Inheritance used for common script functionality
- **Serialization**: All nodes support serialization for debugging

### Testing Architecture Philosophy

The testing framework supports multiple approaches:
- **Unit Testing**: Fast, isolated rule validation
- **Integration Testing**: Multi-rule interaction validation
- **Configuration Testing**: JSON-driven test case definitions
- **Fixture Sharing**: Common test data and utilities

This architecture enables comprehensive validation while maintaining flexibility for different testing needs.

## Success Criteria for AI Agents

This document provides AI agents with:
- **Clear Entry Points**: Know where to start when modifying the system
- **Technical Debt Awareness**: Understanding of current issues and workarounds
- **Architecture Understanding**: Deep knowledge of visitor pattern and object model
- **Testing Guidance**: How to test changes across multiple testing approaches
- **Integration Knowledge**: How the system works with external tools and CI/CD
- **Real-World Constraints**: Understanding of Poetry, GitHub Actions, and file system dependencies
