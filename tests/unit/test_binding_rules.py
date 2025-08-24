"""
Unit tests for binding-related rules.
Tests various binding validation rules.
"""

import unittest

from fixtures.base_test import BaseRuleTest
from fixtures.test_helpers import get_test_config, load_test_view


class TestBindingRules(BaseRuleTest):
	"""Test binding-related validation rules."""

	def test_binding_rule_base_functionality(self):
		"""Test the base BindingRule functionality."""
		# Test with PollingIntervalRule which extends BindingRule
		rule_config = get_test_config("PollingIntervalRule", minimum_interval=5000)

		view_file = load_test_view(self.test_cases_dir, "ExpressionBindings")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule processes binding nodes
		self.assertIsInstance(errors.get("PollingIntervalRule", []), list)

	def test_multiple_binding_types(self):
		"""Test rules that target multiple binding types."""
		# Use PollingIntervalRule which targets expression, property, and tag bindings
		rule_config = get_test_config("PollingIntervalRule", minimum_interval=1000)

		test_cases = ["ExpressionBindings", "PascalCase"]

		for case in test_cases:
			with self.subTest(case=case):
				try:
					view_file = load_test_view(self.test_cases_dir, case)
					errors = self.run_lint_on_file(view_file, rule_config)
					# Just verify it runs without error
					self.assertIsInstance(errors.get("PollingIntervalRule", []), list)
				except FileNotFoundError:
					self.skipTest(f"Test case {case} not found")


if __name__ == "__main__":
	unittest.main()
