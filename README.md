# Ignition Lint Documentation

## Overview

Ignition Lint is a Python framework designed to analyze and lint Ignition Perspective view.json files. It provides a structured way to parse view files, build an object model representation, and apply customizable linting rules to ensure code quality and consistency across your Ignition projects.

## Getting Started with Poetry

### Prerequisites
- Python 3.8 or higher
- Poetry >= 2.0 (install from [python-poetry.org](https://python-poetry.org/docs/#installation))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/design-group/ignition-lint.git
   cd ignition-lint
   ```

2. **Install dependencies with Poetry:**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

4. **Verify installation:**
   ```bash
   poetry run python -m ignition_lint.main --help
   ```

### Development Setup

For development work, install with development dependencies:

```bash
# Install all dependencies including dev tools
poetry install --with dev

# Run tests
poetry run pytest

# Run linting
poetry run pylint ignition_lint/

# Format code
poetry run black ignition_lint/
```

### Running Without Activating Shell

You can run commands directly through Poetry without activating the shell:

```bash
# Run linting on a view file
poetry run python -m ignition_lint.main path/to/view.json

# Run with custom configuration
poetry run python -m ignition_lint.main --config my_rules.json --files "views/**/view.json"
```

### Building and Distribution

```bash
# Build the package
poetry build

# Install locally for testing
poetry install

# Export requirements.txt for CI/CD or Docker
poetry export --output requirements.txt --without-hashes
```

## Key Features

- **Object Model Representation**: Converts flattened JSON structures into a hierarchical object model
- **Extensible Rule System**: Easy-to-extend framework for creating custom linting rules
- **Built-in Rules**: Includes rules for script validation (via Pylint) and binding checks
- **Batch Processing**: Efficiently processes multiple scripts and files in a single run
- **Pre-commit Integration**: Can be integrated into your Git workflow

## Architecture

### Core Components

```
ignition_lint/
├── common/          # Utilities for JSON processing
├── model/           # Object model definitions
├── rules/           # Linting rule implementations
├── linter.py        # Main linting engine
└── main.py          # CLI entry point
```

### Object Model

The framework decompiles Ignition Perspective views into a structured object model with the following node types:

#### Base Classes
- **ViewNode**: Abstract base class for all nodes in the view tree
- **Visitor**: Interface for implementing the visitor pattern

#### Component Nodes
- **Component**: Represents UI components with properties and metadata
- **Property**: Individual component properties

#### Binding Nodes
- **Binding**: Base class for all binding types
- **ExpressionBinding**: Expression-based bindings
- **PropertyBinding**: Property-to-property bindings
- **TagBinding**: Tag-based bindings

#### Script Nodes
- **Script**: Base class for all script types
- **MessageHandlerScript**: Scripts that handle messages
- **CustomMethodScript**: Custom component methods
- **TransformScript**: Script transforms in bindings
- **EventHandlerScript**: Event handler scripts

#### Event Nodes
- **EventHandler**: Base class for event handlers

## How It Works

### 1. JSON Flattening

The framework first flattens the hierarchical view.json structure into path-value pairs:

```python
# Original JSON
{
  "root": {
    "children": [{
      "meta": {"name": "Button"},
      "props": {"text": "Click Me"}
    }]
  }
}

# Flattened representation
{
  "root.children[0].meta.name": "Button",
  "root.children[0].props.text": "Click Me"
}
```

### 2. Model Building

The `ViewModelBuilder` class parses the flattened JSON and constructs the object model:

```python
from ignition_lint.common.flatten_json import flatten_file
from ignition_lint.model import ViewModelBuilder

# Flatten the JSON file
flattened_json = flatten_file("path/to/view.json")

# Build the object model
builder = ViewModelBuilder()
model = builder.build_model(flattened_json)

# Access different node types
components = model['components']
bindings = model['bindings']
scripts = model['scripts']
```

### 3. Rule Application

Rules are applied using the visitor pattern, allowing each rule to process relevant nodes:

```python
from ignition_lint.linter import ViewLinter
from ignition_lint.rules import PylintScriptRule, PollingIntervalRule

# Create linter with rules
linter = ViewLinter()
linter.register_rule(PylintScriptRule())
linter.register_rule(PollingIntervalRule(min_interval=10000))

# Run linting
errors = linter.lint(flattened_json)
```

## Understanding the Visitor Pattern

### What is the Visitor Pattern?

The Visitor pattern is a behavioral design pattern that lets you separate algorithms from the objects on which they operate. In Ignition Lint, it allows you to define new operations (linting rules) without changing the node classes.

### How It Works in Ignition Lint

1. **Node Classes**: Each node type (Component, Binding, Script, etc.) has an `accept()` method that takes a visitor
2. **Visitor Interface**: The `Visitor` base class defines visit methods for each node type
3. **Double Dispatch**: When a node accepts a visitor, it calls the appropriate visit method on that visitor

Here's the flow:

```python
# 1. The linter calls accept on a node
node.accept(rule)

# 2. The node's accept method calls back to the visitor
def accept(self, visitor):
    return visitor.visit_component(self)  # for a Component node

# 3. The visitor's method processes the node
def visit_component(self, component):
    # Your rule logic here
    pass
```

### Why Use the Visitor Pattern?

- **Separation of Concerns**: Node structure is separate from operations
- **Easy Extension**: Add new rules without modifying node classes
- **Type Safety**: Each node type has its own visit method
- **Flexible Processing**: Rules can choose which nodes to process

## Creating Custom Rules - Deep Dive

### What You Have Access To

When writing a custom rule, you have access to extensive information about each node:

#### Component Nodes

```python
class MyComponentRule(LintingRule):
    def visit_component(self, component):
        # Available properties:
        component.path      # Full path in the view: "root.children[0].components.Label"
        component.name      # Component name: "Label_1"
        component.type      # Component type: "ia.display.label"
        component.properties # Dict of all component properties
        
        # Example: Check component positioning
        x_position = component.properties.get('position.x', 0)
        y_position = component.properties.get('position.y', 0)
        
        if x_position < 0 or y_position < 0:
            self.errors.append(
                f"{component.path}: Component '{component.name}' has negative position"
            )
```

#### Binding Nodes

```python
class MyBindingRule(LintingRule):
    def visit_expression_binding(self, binding):
        # Available for all bindings:
        binding.path         # Path to the bound property
        binding.binding_type # Type of binding: "expr", "property", "tag"
        binding.config       # Full binding configuration dict
        
        # Specific to expression bindings:
        binding.expression   # The expression string
        
        # Example: Check for hardcoded values in expressions
        if '"localhost"' in binding.expression or "'localhost'" in binding.expression:
            self.errors.append(
                f"{binding.path}: Expression contains hardcoded localhost"
            )
    
    def visit_tag_binding(self, binding):
        # Specific to tag bindings:
        binding.tag_path    # The tag path string
        
        # Example: Ensure tags follow naming convention
        if not binding.tag_path.startswith("[default]"):
            self.errors.append(
                f"{binding.path}: Tag binding should use [default] provider"
            )
```

#### Script Nodes

```python
class MyScriptRule(LintingRule):
    def visit_custom_method(self, method):
        # Available properties:
        method.path         # Path to the method
        method.name         # Method name: "refreshData"
        method.script         # Raw script code
        method.params       # List of parameter names
        
        # Special method:
        formatted_script = method.get_formatted_script()
        # Returns properly formatted Python with function definition
        
        # Example: Check for print statements
        if 'print(' in method.script:
            self.errors.append(
                f"{method.path}: Method '{method.name}' contains print statement"
            )
    
    def visit_message_handler(self, handler):
        # Additional properties:
        handler.message_type # The message type this handles
        handler.scope        # Dict with scope settings:
                            # {'page': False, 'session': True, 'view': False}
        
        # Example: Warn about session-scoped handlers
        if handler.scope.get('session', False):
            self.errors.append(
                f"{handler.path}: Message handler '{handler.message_type}' "
                f"uses session scope - ensure this is intentional"
            )
```

### Advanced Rule Patterns

#### Pattern 1: Cross-Node Validation

```python
class CrossReferenceRule(LintingRule):
    def __init__(self):
        super().__init__(node_types=[Component, PropertyBinding])
        self.component_paths = set()
        self.binding_targets = []
    
    def visit_component(self, component):
        # Collect all component paths
        self.component_paths.add(component.path)
    
    def visit_property_binding(self, binding):
        # Store binding for later validation
        self.binding_targets.append((binding.path, binding.target_path))
    
    def process_collected_scripts(self):
        # This method is called after all nodes are visited
        for binding_path, target_path in self.binding_targets:
            if target_path not in self.component_paths:
                self.errors.append(
                    f"{binding_path}: Binding targets non-existent component"
                )
```

#### Pattern 2: Context-Aware Rules

```python
class ContextAwareRule(LintingRule):
    def __init__(self):
        super().__init__(node_types=[Component, Script])
        self.current_component = None
        self.component_stack = []
    
    def visit_component(self, component):
        # Track component context
        self.component_stack.append(component)
        self.current_component = component
    
    def visit_script(self, script_obj):
        # Use component context
        if self.current_component and self.current_component.type == "ia.display.table":
            if "selectedRow" in script_obj.script and "rowData" not in script_obj.script:
                self.errors.append(
                    f"{script_obj.path}: Table script uses selectedRow without rowData check"
                )
```

#### Pattern 3: Statistical Analysis

```python
class ComplexityAnalysisRule(LintingRule):
    def __init__(self, max_complexity_score=100):
        super().__init__(node_types=[Component])
        self.max_complexity = max_complexity_score
        self.complexity_scores = {}
    
    def visit_component(self, component):
        score = 0
        
        # Calculate complexity based on various factors
        score += len(component.properties) * 2  # Property count
        
        # Check for deeply nested properties
        for prop_name in component.properties:
            score += prop_name.count('.') * 3  # Nesting depth
        
        # Store score
        self.complexity_scores[component.path] = score
        
        if score > self.max_complexity:
            self.errors.append(
                f"{component.path}: Component complexity score {score} "
                f"exceeds maximum {self.max_complexity}"
            )
```

### Accessing Raw JSON Data

Sometimes you need access to the original flattened JSON data:

```python
class RawDataRule(LintingRule):
    def __init__(self):
        super().__init__()
        self.flattened_json = None
    
    def lint(self, flattened_json):
        # Store the flattened JSON for use in visit methods
        self.flattened_json = flattened_json
        return super().lint(flattened_json)
    
    def visit_component(self, component):
        # Access any part of the flattened JSON
        style_classes = self.flattened_json.get(
            f"{component.path}.props.style.classes", 
            ""
        )
        
        if style_classes and "/" in style_classes:
            self.errors.append(
                f"{component.path}: Style classes contain invalid '/' character"
            )
```

### Rule Lifecycle Methods

```python
class LifecycleAwareRule(LintingRule):
    def __init__(self):
        super().__init__()
        self.setup_complete = False
    
    def before_visit(self):
        """Called before visiting any nodes."""
        self.setup_complete = True
        self.errors = []  # Reset errors
    
    def visit_component(self, component):
        """Process each component."""
        # Your logic here
        pass
    
    def process_collected_scripts(self):
        """Called after all nodes are visited."""
        # Batch processing, cross-validation, etc.
        pass
    
    def after_visit(self):
        """Called after all processing is complete."""
        # Cleanup, summary generation, etc.
        pass
```

## Node Properties Reference

### Component
- `path`: Full path to the component
- `name`: Component instance name
- `type`: Component type (e.g., "ia.display.label")
- `properties`: Dictionary of all component properties
- `children`: List of child components (if container)

### ExpressionBinding
- `path`: Path to the bound property
- `expression`: The expression string
- `binding_type`: Always "expr"
- `config`: Full binding configuration

### PropertyBinding
- `path`: Path to the bound property
- `target_path`: Path to the source property
- `binding_type`: Always "property"
- `config`: Full binding configuration

### TagBinding
- `path`: Path to the bound property
- `tag_path`: The tag path string
- `binding_type`: Always "tag"
- `config`: Full binding configuration

### MessageHandlerScript
- `path`: Path to the handler
- `script`: Script string
- `message_type`: Type of message handled
- `scope`: Scope configuration dict
- `get_formatted_script()`: Returns formatted Python code

### CustomMethodScript
- `path`: Path to the method
- `name`: Method name
- `script`: Script string
- `params`: List of parameter names
- `get_formatted_script()`: Returns formatted Python code

### TransformScript
- `path`: Path to the transform
- `script`: Script string
- `binding_path`: Path to parent binding
- `get_formatted_script()`: Returns formatted Python code

### EventHandlerScript
- `path`: Path to the handler
- `event_type`: Event type (e.g., "onClick")
- `script`: Script string
- `scope`: Scope setting ("L", "P", "S")
- `get_formatted_script()`: Returns formatted Python code

## Built-in Rules

### PylintScriptRule
Runs Pylint on all scripts in the view to check for:
- Undefined variables
- Unused imports
- Syntax errors

### PollingIntervalRule
Ensures that polling intervals in expressions meet minimum requirements:
- Checks `now()` function calls
- Validates interval values
- Default minimum: 10,000ms

## CLI Usage

### Basic Usage

```bash
# Using Poetry (recommended)
poetry run python -m ignition_lint.main path/to/view.json

# Lint multiple files with glob pattern
poetry run python -m ignition_lint.main --files "**/view.json"

# Use custom configuration
poetry run python -m ignition_lint.main --config my_rules.json --files "views/**/view.json"

# If you've activated the Poetry shell
poetry shell
python -m ignition_lint.main path/to/view.json
```

### Pre-commit Integration

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/design-group/ignition-lint
    rev: v0.1.0
    hooks:
      - id: ignition-lint
        args: [
          "--component-style", "PascalCase",
          "--parameter-style", "camelCase",
          "--allow-acronyms",
        ]
        files: view\.json$
```

## Best Practices

1. **Rule Granularity**: Keep rules focused on a single concern
2. **Performance**: Use batch processing for operations like script analysis
3. **Error Messages**: Provide clear, actionable error messages with paths
4. **Configuration**: Make rules configurable for different project requirements
5. **Testing**: Test rules with various edge cases and malformed inputs
6. **Node Type Selection**: Only register for node types you actually need to process

## Future Enhancements

The framework is designed to be extended with:
- Additional node types (e.g., style classes, custom properties)
- More sophisticated analysis rules
- Integration with CI/CD pipelines
- Performance metrics and reporting
- Auto-fix capabilities for certain rule violations

## Contributing

When adding new features:
1. Follow the existing object model patterns
2. Implement the visitor pattern for new node types
3. Provide configuration options for new rules
4. Document rule behavior and configuration
5. Add appropriate error handling

### Development Workflow

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/ignition-lint.git
cd ignition-lint

# Install development dependencies
poetry install --with dev

# Create a feature branch
git checkout -b feature/my-new-feature

# Make your changes and test
poetry run pytest
poetry run pylint ignition_lint/

# Commit and push
git commit -m "Add new feature"
git push origin feature/my-new-feature
```
