#!/usr/bin/env python3
"""Debug the golden file test setup."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ignition_lint.rules import RULES_MAP
from ignition_lint.linter import LintEngine
from ignition_lint.common.flatten_json import read_json_file, flatten_json

print("=== Debug Golden File Test Setup ===")

# Check what rules are available
print(f"Available rules: {len(RULES_MAP)}")
for rule_name, rule_class in RULES_MAP.items():
	print(f"  - {rule_name}: {rule_class}")

print("\n=== Creating Rules ===")
rules = []
for rule_name, rule_class in RULES_MAP.items():
	try:
		rule = rule_class.create_from_config({})
		rules.append(rule)
		print(f"✅ Created rule: {rule_name}")
	except Exception as e:
		print(f"❌ Failed to create rule {rule_name}: {e}")

print(f"\nTotal rules created: {len(rules)}")

# Create lint engine
lint_engine = LintEngine(rules)

# Test on PascalCase
print("\n=== Testing on PascalCase ===")
test_case_dir = Path('tests/cases/PascalCase')
view_file = test_case_dir / 'view.json'

if view_file.exists():
	json_data = read_json_file(view_file)
	flattened_json = flatten_json(json_data)

	lint_engine.flattened_json = flattened_json
	lint_engine.view_model = lint_engine._get_view_model()
	model = lint_engine._serialize_view_model()
	stats = lint_engine.get_model_statistics(flattened_json)

	print(f"Flattened JSON keys: {len(flattened_json)}")
	print(f"Model keys: {list(model.keys())}")
	print(f"Total nodes: {stats.get('total_nodes', 'N/A')}")

	for key, section in model.items():
		count = section.get('count', 0)
		if count > 0:
			print(f"  {key}: {count} nodes")
else:
	print(f"❌ View file not found: {view_file}")
