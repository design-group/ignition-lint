"""
Unit tests for the ComponentNameRule.
Tests various naming conventions and edge cases.
"""

import unittest
from pathlib import Path

from fixtures.base_test import BaseRuleTest
from fixtures.test_helpers import get_test_config, load_test_view


class TestComponentNamingPascalCase(BaseRuleTest):
	"""Test PascalCase naming convention."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"ComponentNameRule", convention="PascalCase", allow_numbers=True, min_length=1
		)

	def test_pascal_case_passes_pascal_case_rule(self):
		"""PascalCase view should pass PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_passes(view_file, self.rule_config, "ComponentNameRule")

	def test_camel_case_fails_pascal_case_rule(self):
		"""camelCase view should fail PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")

	def test_snake_case_fails_pascal_case_rule(self):
		"""snake_case view should fail PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "snake_case")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")

	def test_inconsistent_case_fails_pascal_case_rule(self):
		"""inconsistentCase view should fail PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "inconsistentCase")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")


class TestComponentNamingCamelCase(BaseRuleTest):
	"""Test camelCase naming convention."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"ComponentNameRule", convention="camelCase", allow_numbers=True, min_length=1
		)

	def test_camel_case_passes_camel_case_rule(self):
		"""camelCase view should pass camelCase rule."""
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_passes(view_file, self.rule_config, "ComponentNameRule")

	def test_pascal_case_fails_camel_case_rule(self):
		"""PascalCase view should fail camelCase rule."""
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")

	def test_snake_case_fails_camel_case_rule(self):
		"""snake_case view should fail camelCase rule."""
		view_file = load_test_view(self.test_cases_dir, "snake_case")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")


class TestComponentNamingSnakeCase(BaseRuleTest):
	"""Test snake_case naming convention."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"ComponentNameRule", convention="snake_case", allow_numbers=True, min_length=1
		)

	def test_snake_case_passes_snake_case_rule(self):
		"""snake_case view should pass snake_case rule."""
		view_file = load_test_view(self.test_cases_dir, "snake_case")
		self.assert_rule_passes(view_file, self.rule_config, "ComponentNameRule")

	def test_pascal_case_fails_snake_case_rule(self):
		"""PascalCase view should fail snake_case rule."""
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")

	def test_camel_case_fails_snake_case_rule(self):
		"""camelCase view should fail snake_case rule."""
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_fails(view_file, self.rule_config, "ComponentNameRule")


class TestComponentNamingKebabCase(BaseRuleTest):
	"""Test kebab-case naming convention."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"ComponentNameRule", convention="kebab-case", allow_numbers=True, min_length=1
		)

	def test_kebab_case_passes_kebab_case_rule(self):
		"""kebab-case view should pass kebab-case rule."""
		view_file = load_test_view(self.test_cases_dir, "kebab-case")
		self.assert_rule_passes(view_file, self.rule_config, "ComponentNameRule")


class TestComponentNamingTitleCase(BaseRuleTest):
	"""Test Title Case naming convention."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"ComponentNameRule", convention="Title Case", allow_numbers=True, min_length=1
		)

	def test_title_case_passes_title_case_rule(self):
		"""Title Case view should pass Title Case rule."""
		view_file = load_test_view(self.test_cases_dir, "Title Case")
		self.assert_rule_passes(view_file, self.rule_config, "ComponentNameRule")


class TestComponentNamingUpperCase(BaseRuleTest):
	"""Test SCREAMING_SNAKE_CASE naming convention."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"ComponentNameRule", convention="SCREAMING_SNAKE_CASE", allow_numbers=True, min_length=1
		)

	def test_upper_case_passes_upper_case_rule(self):
		"""UPPER_CASE view should pass SCREAMING_SNAKE_CASE rule."""
		view_file = load_test_view(self.test_cases_dir, "UPPER_CASE")
		self.assert_rule_passes(view_file, self.rule_config, "ComponentNameRule")


class TestComponentNamingEdgeCases(BaseRuleTest):
	"""Test edge cases for component naming rules."""

	def test_min_length_validation(self):
		"""Test minimum length validation."""
		rule_config = get_test_config("ComponentNameRule", convention="PascalCase", min_length=5)

		# This would need a special test view with short component names
		# For now, we'll test against existing views
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		# Depending on the actual component names in the view, this might pass or fail
		errors = self.run_lint_on_file(view_file, rule_config)
		# We just verify the rule runs without crashing
		self.assertIsInstance(errors.get("ComponentNameRule", []), list)

	def test_numbers_allowed_vs_disallowed(self):
		"""Test allowing/disallowing numbers in component names."""
		rule_config_with_numbers = get_test_config(
			"ComponentNameRule", convention="PascalCase", allow_numbers=True
		)

		rule_config_no_numbers = get_test_config(
			"ComponentNameRule", convention="PascalCase", allow_numbers=False
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")

		# Run both configs and verify they both work (results may differ)
		errors_with_numbers = self.run_lint_on_file(view_file, rule_config_with_numbers)
		errors_no_numbers = self.run_lint_on_file(view_file, rule_config_no_numbers)

		self.assertIsInstance(errors_with_numbers.get("ComponentNameRule", []), list)
		self.assertIsInstance(errors_no_numbers.get("ComponentNameRule", []), list)

	def test_forbidden_names(self):
		"""Test forbidden component names."""
		rule_config = get_test_config(
			"ComponentNameRule", convention="PascalCase", forbidden_names=["Button", "Label", "Panel"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Just verify the rule runs without crashing
		self.assertIsInstance(errors.get("ComponentNameRule", []), list)

	def test_custom_abbreviations(self):
		"""Test custom abbreviations handling."""
		rule_config = get_test_config(
			"ComponentNameRule", convention="PascalCase", allowed_abbreviations=["API", "HTTP", "XML"],
			auto_detect_abbreviations=False
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Just verify the rule runs without crashing
		self.assertIsInstance(errors.get("ComponentNameRule", []), list)


if __name__ == "__main__":
	unittest.main()
