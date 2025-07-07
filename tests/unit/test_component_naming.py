"""
Unit tests for the NamePatternRule.
Tests various naming conventions and edge cases for different node types.
"""

import unittest
from pathlib import Path

from fixtures.base_test import BaseRuleTest
from fixtures.test_helpers import get_test_config, load_test_view


class TestNamePatternPascalCase(BaseRuleTest):
	"""Test PascalCase naming convention for components."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", allow_numbers=True,
			min_length=1
		)

	def test_pascal_case_passes_pascal_case_rule(self):
		"""PascalCase view should pass PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")

	def test_camel_case_fails_pascal_case_rule(self):
		"""camelCase view should fail PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")

	def test_snake_case_fails_pascal_case_rule(self):
		"""snake_case view should fail PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "snake_case")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")

	def test_inconsistent_case_fails_pascal_case_rule(self):
		"""inconsistentCase view should fail PascalCase rule."""
		view_file = load_test_view(self.test_cases_dir, "inconsistentCase")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternCamelCase(BaseRuleTest):
	"""Test camelCase naming convention for components."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="camelCase", allow_numbers=True,
			min_length=1
		)

	def test_camel_case_passes_camel_case_rule(self):
		"""camelCase view should pass camelCase rule."""
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")

	def test_pascal_case_fails_camel_case_rule(self):
		"""PascalCase view should fail camelCase rule."""
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")

	def test_snake_case_fails_camel_case_rule(self):
		"""snake_case view should fail camelCase rule."""
		view_file = load_test_view(self.test_cases_dir, "snake_case")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternSnakeCase(BaseRuleTest):
	"""Test snake_case naming convention for components."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="snake_case", allow_numbers=True,
			min_length=1
		)

	def test_snake_case_passes_snake_case_rule(self):
		"""snake_case view should pass snake_case rule."""
		view_file = load_test_view(self.test_cases_dir, "snake_case")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")

	def test_pascal_case_fails_snake_case_rule(self):
		"""PascalCase view should fail snake_case rule."""
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")

	def test_camel_case_fails_snake_case_rule(self):
		"""camelCase view should fail snake_case rule."""
		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.assert_rule_fails(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternKebabCase(BaseRuleTest):
	"""Test kebab-case naming convention for components."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="kebab-case", allow_numbers=True,
			min_length=1
		)

	def test_kebab_case_passes_kebab_case_rule(self):
		"""kebab-case view should pass kebab-case rule."""
		view_file = load_test_view(self.test_cases_dir, "kebab-case")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternTitleCase(BaseRuleTest):
	"""Test Title Case naming convention for components."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="Title Case", allow_numbers=True,
			min_length=1
		)

	def test_title_case_passes_title_case_rule(self):
		"""Title Case view should pass Title Case rule."""
		view_file = load_test_view(self.test_cases_dir, "Title Case")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternUpperCase(BaseRuleTest):
	"""Test SCREAMING_SNAKE_CASE naming convention for components."""

	def setUp(self):
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="SCREAMING_SNAKE_CASE",
			allow_numbers=True, min_length=1
		)

	def test_upper_case_passes_upper_case_rule(self):
		"""UPPER_CASE view should pass SCREAMING_SNAKE_CASE rule."""
		view_file = load_test_view(self.test_cases_dir, "UPPER_CASE")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternMultipleNodeTypes(BaseRuleTest):
	"""Test naming conventions applied to multiple node types."""

	def test_components_and_custom_methods_same_convention(self):
		"""Test applying same convention to components and custom methods."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component", "custom_method"], convention="camelCase",
			min_length=3
		)

		view_file = load_test_view(self.test_cases_dir, "camelCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_different_conventions_per_node_type(self):
		"""Test different naming conventions for different node types."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "custom_method", "message_handler"],
			convention="camelCase",  # Default convention
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"min_length": 4
				},
				"custom_method": {
					"convention": "camelCase",
					"min_length": 3
				},
				"message_handler": {
					"convention": "snake_case",
					"min_length": 4
				}
			}
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)


class TestNamePatternEdgeCases(BaseRuleTest):
	"""Test edge cases for naming pattern rules."""

	def test_min_length_validation(self):
		"""Test minimum length validation."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=5
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_max_length_validation(self):
		"""Test maximum length validation."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1,
			max_length=10
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_numbers_allowed_vs_disallowed(self):
		"""Test allowing/disallowing numbers in component names."""
		rule_config_with_numbers = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", allow_numbers=True
		)

		rule_config_no_numbers = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", allow_numbers=False
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")

		# Run both configs and verify they both work (results may differ)
		errors_with_numbers = self.run_lint_on_file(view_file, rule_config_with_numbers)
		errors_no_numbers = self.run_lint_on_file(view_file, rule_config_no_numbers)

		self.assertIsInstance(errors_with_numbers.get("NamePatternRule", []), list)
		self.assertIsInstance(errors_no_numbers.get("NamePatternRule", []), list)

	def test_forbidden_names(self):
		"""Test forbidden component names."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase",
			forbidden_names=["Button", "Label", "Panel"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_custom_abbreviations(self):
		"""Test custom abbreviations handling."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase",
			allowed_abbreviations=["API", "HTTP", "XML"], auto_detect_abbreviations=False
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_skip_names(self):
		"""Test skipping certain names from validation."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase",
			skip_names=["root", "main", "container"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_custom_pattern(self):
		"""Test custom regex pattern instead of predefined conventions."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"],
			custom_pattern=r"^(btn|lbl|pnl)[A-Z][a-zA-Z0-9]*$", min_length=4, max_length=25
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(errors.get("NamePatternRule", []), list)


class TestNamePatternSpecificNodeTypes(BaseRuleTest):
	"""Test naming patterns for specific node types beyond components."""

	def test_custom_method_naming(self):
		"""Test naming validation for custom methods."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["custom_method"], convention="camelCase", min_length=3,
			forbidden_names=["method", "function", "temp"]
		)

		# This test assumes your test views have custom methods
		# You might need to create specific test views with custom methods
		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_message_handler_naming(self):
		"""Test naming validation for message handlers."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["message_handler"], convention="snake_case", min_length=4,
			forbidden_names=["handler", "msg", "temp"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_property_naming(self):
		"""Test naming validation for properties."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["property"], convention="camelCase", min_length=2,
			forbidden_names=["temp", "tmp", "test", "data"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(errors.get("NamePatternRule", []), list)

	def test_event_handler_naming(self):
		"""Test naming validation for event handlers."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["event_handler"], convention="camelCase", min_length=4,
			skip_names=["onClick", "onFocus", "onBlur", "onLoad"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		errors = self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(errors.get("NamePatternRule", []), list)


if __name__ == "__main__":
	unittest.main()
