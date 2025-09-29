#!/usr/bin/env python3
"""Simple debug test to isolate the golden file issue."""

import json
import sys
from pathlib import Path

from ignition_lint.common.flatten_json import read_json_file, flatten_json
from ignition_lint.linter import LintEngine
from ignition_lint.rules import RULES_MAP

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def create_lint_engine():
	"""Create lint engine like the test does."""
	rules = []
	for rule_name, rule_class in RULES_MAP.items():
		try:
			rule = rule_class.create_from_config({})
			rules.append(rule)
		except Exception as e:
			print(f"Warning: Could not create rule {rule_name}: {e}")

	return LintEngine(rules)


def test_pascalcase_model():
	"""Test PascalCase model generation."""
	print("=== Testing PascalCase Model Generation ===")

	# Create lint engine
	lint_engine = create_lint_engine()

	# Load test case
	view_file = Path('tests/cases/PascalCase/view.json')
	golden_file = Path('tests/cases/PascalCase/debug/model.json')

	# Generate current model (exactly like the test does)
	json_data = read_json_file(view_file)
	flattened_json = flatten_json(json_data)

	lint_engine.flattened_json = flattened_json
	lint_engine.view_model = lint_engine.get_view_model()
	current_model = lint_engine.serialize_view_model()

	# Load golden file
	with open(golden_file, 'r', encoding='utf-8') as f:
		expected_model = json.load(f)

	print("Current model summary:")
	for key, section in current_model.items():
		count = section.get('count', 0)
		if count > 0:
			print(f"  {key}: {count} nodes")

	print("\nExpected model summary:")
	for key, section in expected_model.items():
		count = section.get('count', 0)
		if count > 0:
			print(f"  {key}: {count} nodes")

	# Compare key counts
	print("\nComparison:")
	all_keys = set(current_model.keys()) | set(expected_model.keys())
	for key in sorted(all_keys):
		current_count = current_model.get(key, {}).get('count', 0)
		expected_count = expected_model.get(key, {}).get('count', 0)
		match = "✅" if current_count == expected_count else "❌"
		print(f"  {match} {key}: current={current_count}, expected={expected_count}")


if __name__ == "__main__":
	test_pascalcase_model()
