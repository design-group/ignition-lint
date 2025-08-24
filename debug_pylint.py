#!/usr/bin/env python3
"""Debug script to test PylintScriptRule directly"""

from ignition_lint.common.flatten_json import read_json_file, flatten_json
from ignition_lint.model.builder import ViewModelBuilder
from ignition_lint.rules.lint_script import PylintScriptRule

# Load and process a view with scripts
json_data = read_json_file('tests/cases/ExpressionBindings/view.json')
flattened = flatten_json(json_data)
builder = ViewModelBuilder()
model = builder.build_model(flattened)

# Create all nodes list
all_nodes = []
for node_list in model.values():
	all_nodes.extend(node_list)

# Create and test PylintScriptRule
rule = PylintScriptRule()
print(f"Rule created. Debug enabled: {rule.debug}")
print(f"Rule target types: {[nt.value for nt in rule.target_node_types]}")

# Check what script nodes exist
script_nodes = [node for node in all_nodes if rule.applies_to(node)]
print(f"Script nodes found: {len(script_nodes)}")

for node in script_nodes:
	from ignition_lint.model.node_types import ScriptNode
	print(f"  - {node.path} ({type(node).__name__})")
	print(f"    isinstance ScriptNode: {isinstance(node, ScriptNode)}")
	print(f"    MRO: {[cls.__name__ for cls in type(node).__mro__]}")
	print()

# Test visit methods manually
print("Testing visit methods manually...")
for node in script_nodes[:2]:  # Just test first 2
	print(f"Visiting {node.path}")
	if hasattr(node, 'accept'):
		print(f"  Node has accept method")
		node.accept(rule)
	else:
		print(f"  Node missing accept method")

print(f"After manual visits - Collected scripts: {len(rule.collected_scripts)}")

# Reset and try process_nodes
rule.collected_scripts = {}
print("Processing nodes...")
rule.process_nodes(all_nodes)

print(f"Collected scripts: {len(rule.collected_scripts)}")
for path, node in rule.collected_scripts.items():
	print(f"  - {path}: {node.script[:30]}...")

print(f"Errors found: {len(rule.errors)}")
print(f"Warnings found: {len(rule.warnings)}")

for error in rule.errors:
	print(f"Error: {error}")

for warning in rule.warnings:
	print(f"Warning: {warning}")
