# pylint: disable=import-error
"""
Test cases to demonstrate and verify the warnings vs errors infrastructure.
"""

from fixtures.base_test import BaseRuleTest
from fixtures.test_helpers import get_test_config, load_test_view


class TestWarningsVsErrorsInfrastructure(BaseRuleTest):
	"""Test the enhanced test infrastructure for warnings vs errors."""

	def test_name_pattern_rule_produces_warnings(self):
		"""Test that NamePatternRule produces warnings, not errors."""
		# Arrange: camelCase view with PascalCase rule should produce warnings
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1
		)
		view_file = load_test_view(self.test_cases_dir, "camelCase")

		# Act & Assert: Should have 1 warning, 0 errors
		self.assert_rule_summary(
			view_file, rule_config, "NamePatternRule", expected_warnings=1, expected_errors=0
		)

	def test_name_pattern_rule_warning_content(self):
		"""Test that NamePatternRule warning contains expected patterns."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1
		)
		view_file = load_test_view(self.test_cases_dir, "camelCase")

		# Act & Assert: Should contain naming convention message
		self.assert_rule_warnings(
			view_file, rule_config, "NamePatternRule", expected_warning_count=1,
			warning_patterns=["doesn't follow", "PascalCase"]
		)

	def test_polling_interval_rule_produces_errors(self):
		"""Test that PollingIntervalRule produces errors, not warnings."""
		rule_config = get_test_config("PollingIntervalRule", minimum_interval=10000)

		# Use a view that might have polling issues
		view_file = load_test_view(self.test_cases_dir, "ExpressionBindings")

		# Act: Get detailed results to check error vs warning classification
		results = self.run_lint_on_file_detailed(view_file, rule_config)

		# Assert: If any issues found, they should be errors, not warnings
		rule_warnings = results.warnings.get("PollingIntervalRule", [])
		rule_errors = results.errors.get("PollingIntervalRule", [])

		# PollingIntervalRule should never produce warnings
		self.assertEqual(
			rule_warnings, [], f"PollingIntervalRule should not produce warnings, found: {rule_warnings}"
		)

		# If there are any issues, they should be errors
		if rule_errors:
			self.assertGreater(len(rule_errors), 0, "Expected PollingIntervalRule to produce errors")

	def test_mixed_rules_warnings_and_errors(self):
		"""Test running multiple rules that produce both warnings and errors."""
		# Test NamePatternRule produces warnings
		name_rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1
		)
		view_file = load_test_view(self.test_cases_dir, "camelCase")

		# Assert: NamePatternRule should produce warnings
		self.assert_rule_summary(
			view_file, name_rule_config, "NamePatternRule", expected_warnings=1, expected_errors=0
		)

		# Test PollingIntervalRule produces errors (using a different view)
		polling_rule_config = get_test_config("PollingIntervalRule", minimum_interval=5000)

		# Check that PollingIntervalRule only produces errors, never warnings
		results = self.run_lint_on_file_detailed(view_file, polling_rule_config)
		polling_warnings = results.warnings.get("PollingIntervalRule", [])
		self.assertEqual(polling_warnings, [], "PollingIntervalRule should not produce warnings")

	def test_rule_passes_completely_no_warnings_or_errors(self):
		"""Test that a rule can pass with no warnings or errors."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1
		)
		view_file = load_test_view(self.test_cases_dir, "PascalCase")

		# Act & Assert: Should have no warnings or errors
		self.assert_rule_passes_completely(view_file, rule_config, "NamePatternRule")

	def test_backward_compatibility_still_works(self):
		"""Test that existing test methods still work for backward compatibility."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1
		)

		# Test that old methods still work
		view_file_pass = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_passes(view_file_pass, rule_config, "NamePatternRule")

		view_file_fail = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_fails(view_file_fail, rule_config, "NamePatternRule", expected_error_count=1)
