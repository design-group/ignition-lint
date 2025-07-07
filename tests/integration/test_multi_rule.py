"""
Integration tests for multiple rules working together.
Tests interactions between different linting rules.
"""

import unittest
from pathlib import Path

from fixtures.base_test import BaseIntegrationTest
from fixtures.test_helpers import get_test_config, load_test_view


class TestMultipleRules(BaseIntegrationTest):
	"""Test multiple rules working together."""

	def test_component_naming_and_polling_rules(self):
		"""Test ComponentNameRule and PollingIntervalRule together."""
		rule_configs = {
			"ComponentNameRule": {
				"enabled": True,
				"kwargs": {
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
		errors = self.run_multiple_rules(view_file, rule_configs)

		# Should successfully run both rules
		self.assertIsInstance(errors, dict)

		# ComponentNameRule should pass for PascalCase view
		component_errors = errors.get("ComponentNameRule", [])
		self.assertEqual(component_errors, [], "ComponentNameRule should pass for PascalCase view")

	def test_all_available_rules_together(self):
		"""Test running all available rules together."""
		rule_configs = {
			"ComponentNameRule": {
				"enabled": True,
				"kwargs": {
					"convention": "PascalCase"
				}
			},
			"PollingIntervalRule": {
				"enabled": True,
				"kwargs": {
					"minimum_interval": 5000
				}
			},
			"PylintScriptRule": {
				"enabled": True,
				"kwargs": {}
			}
		}

		test_cases = ["PascalCase", "camelCase", "ExpressionBindings"]

		for case in test_cases:
			with self.subTest(case=case):
				try:
					view_file = load_test_view(self.test_cases_dir, case)
					errors = self.run_multiple_rules(view_file, rule_configs)

					# Should complete without crashing
					self.assertIsInstance(errors, dict)

					# Verify each rule either passed or failed gracefully
					for rule_name in rule_configs.keys():
						if rule_name in errors:
							rule_errors = errors[rule_name]
							self.assertIsInstance(rule_errors, list)

				except FileNotFoundError:
					self.skipTest(f"Test case {case} not found")

	def test_rule_interactions(self):
		"""Test that rules don't interfere with each other."""
		# Run ComponentNameRule alone
		single_rule_config = {"ComponentNameRule": {"enabled": True, "kwargs": {"convention": "PascalCase"}}}

		# Run ComponentNameRule with other rules
		multi_rule_config = {
			"ComponentNameRule": {
				"enabled": True,
				"kwargs": {
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

		single_errors = self.run_multiple_rules(view_file, single_rule_config)
		multi_errors = self.run_multiple_rules(view_file, multi_rule_config)

		# ComponentNameRule results should be the same in both cases
		single_component_errors = single_errors.get("ComponentNameRule", [])
		multi_component_errors = multi_errors.get("ComponentNameRule", [])

		self.assertEqual(
			single_component_errors, multi_component_errors,
			"ComponentNameRule results should be consistent whether run alone or with other rules"
		)

	def test_error_aggregation(self):
		"""Test that errors from multiple rules are properly aggregated."""
		# Use a view that should fail ComponentNameRule but pass others
		rule_configs = {
			"ComponentNameRule": {
				"enabled": True,
				"kwargs": {
					"convention": "PascalCase"
				}
			},
			"PollingIntervalRule": {
				"enabled": True,
				"kwargs": {
					"minimum_interval": 1000
				}  # Low threshold to avoid errors
			}
		}

		# Test with camelCase view which should fail PascalCase rule
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		errors = self.run_multiple_rules(view_file, rule_configs)

		# Should have ComponentNameRule errors
		component_errors = errors.get("ComponentNameRule", [])
		self.assertGreater(len(component_errors), 0, "Should have ComponentNameRule errors for camelCase view")

		# Calculate total errors
		total_errors = sum(len(rule_errors) for rule_errors in errors.values())
		self.assertGreater(total_errors, 0, "Should have some total errors")


if __name__ == "__main__":
	unittest.main()
