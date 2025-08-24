"""
Unit tests for test discovery and framework functionality.
Tests the test infrastructure itself.
"""

import json
import unittest

from fixtures.base_test import BaseRuleTest
from fixtures.test_helpers import (
	create_mock_view,
	create_temp_view_file,
	get_test_config,
	assert_no_errors,
	assert_rule_errors,
	load_test_view,
)


class TestDiscoveryFunctionality(BaseRuleTest):
	"""Test test discovery and framework functionality."""

	def test_discover_test_cases(self):
		"""Test that test case discovery works correctly."""
		discovered_cases = {}

		if self.test_cases_dir.exists():
			for case_dir in self.test_cases_dir.iterdir():
				if case_dir.is_dir():
					view_files = list(case_dir.glob("**/view.json"))
					if view_files:
						discovered_cases[case_dir.name] = view_files

		# Should find some test cases
		self.assertGreater(len(discovered_cases), 0, "Should discover some test cases")

		# Each discovered case should have at least one view.json file
		for case_name, view_files in discovered_cases.items():
			with self.subTest(case=case_name):
				self.assertGreater(len(view_files), 0, f"Case {case_name} should have view files")
				for view_file in view_files:
					self.assertTrue(view_file.exists(), f"View file should exist: {view_file}")
					self.assertEqual(view_file.name, "view.json", "Should be named view.json")

	def test_config_creation_and_usage(self):
		"""Test creating and using test configurations."""
		config = get_test_config("NamePatternRule", convention="PascalCase")

		expected_config = {"NamePatternRule": {"enabled": True, "kwargs": {"convention": "PascalCase"}}}

		self.assertEqual(config, expected_config)

	def test_mock_view_creation(self):
		"""Test creating mock view files for testing."""
		components = [{
			"name": "TestButton",
			"type": "ia.input.button"
		}, {
			"name": "TestLabel",
			"type": "ia.display.label"
		}]

		view_content = create_mock_view(components)

		# Should be valid JSON
		view_data = json.loads(view_content)
		self.assertEqual(view_data["meta"]["name"], "root")
		self.assertIn("props", view_data)

	def test_temp_view_file_creation(self):
		"""Test creating temporary view files."""
		view_content = create_mock_view([{"name": "TempComponent"}])
		temp_file = create_temp_view_file(view_content)

		try:
			self.assertTrue(temp_file.exists())
			self.assertTrue(temp_file.name.endswith('.json'))

			# Should be able to read it back
			with open(temp_file, 'r', encoding='utf-8') as f:
				loaded_content = f.read()

			self.assertEqual(view_content, loaded_content)
		finally:
			# Clean up
			if temp_file.exists():
				temp_file.unlink()

	def test_helper_assertion_functions(self):
		"""Test the helper assertion functions."""
		# Test assert_no_errors
		empty_errors = {}
		assert_no_errors(empty_errors)

		errors_with_empty_rule = {"SomeRule": []}
		assert_no_errors(errors_with_empty_rule, "SomeRule")

		# Test assert_rule_errors
		errors_with_content = {"TestRule": ["Error 1", "Error containing pattern"]}
		assert_rule_errors(errors_with_content, "TestRule", expected_count=2)
		assert_rule_errors(errors_with_content, "TestRule", error_patterns=["pattern"])

		# Test that assertions work correctly
		with self.assertRaises(AssertionError):
			assert_rule_errors(errors_with_content, "TestRule", expected_count=1)


class TestFrameworkIntegration(BaseRuleTest):
	"""Test integration between different framework components."""

	def test_rule_engine_creation(self):
		"""Test creating lint engines with different rule configurations."""
		configs = [
			get_test_config("NamePatternRule", convention="PascalCase"),
			get_test_config("PollingIntervalRule", minimum_interval=5000),
		]

		for config in configs:
			with self.subTest(config=config):
				lint_engine = self.create_lint_engine(config)
				self.assertIsNotNone(lint_engine)
				self.assertGreater(len(lint_engine.rules), 0)

	def test_multiple_rules_together(self):
		"""Test running multiple rules together."""
		rule_config = {
			"NamePatternRule": {
				"enabled": True,
				"kwargs": {
					"target_node_types": "component",
					"convention": "PascalCase"
				}
			},
			"PollingIntervalRule": {
				"enabled": True,
				"kwargs": {
					"minimum_interval": 10000
				}
			}
		}

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Should be able to run multiple rules without conflicts
		self.assertIsInstance(errors, dict)
		# Both rules should be present in results (even if no errors)
		# Note: Rules only appear in results if they have errors, so we just
		# verify the linting completed successfully
		total_errors = sum(len(rule_errors) for rule_errors in errors.values())
		self.assertIsInstance(total_errors, int)


if __name__ == "__main__":
	unittest.main()
