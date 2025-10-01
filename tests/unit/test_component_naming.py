# pylint: disable=import-error
"""
Unit tests for the NamePatternRule.
Tests various naming conventions and edge cases for different node types.
"""

import unittest

from fixtures.base_test import BaseRuleTest
from fixtures.test_helpers import get_test_config, load_test_view


class TestNamePatternPascalCase(BaseRuleTest):
	"""Test PascalCase naming convention for components."""

	def setUp(self): # pylint: disable=invalid-name
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", allow_numbers=True,
			min_length=1, severity="error"
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
	def setUp(self): # pylint: disable=invalid-name
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="camelCase", allow_numbers=True,
			min_length=1, severity="error"
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

	def setUp(self): # pylint: disable=invalid-name
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="snake_case", allow_numbers=True,
			min_length=1, severity="error"
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

	def setUp(self): # pylint: disable=invalid-name
		super().setUp()
		self.rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="kebab-case", allow_numbers=True,
			min_length=1
		)

	def test_kebab_case_passes_kebab_case_rule(self):
		"""kebab-case view should pass kebab-case rule."""
		view_file = load_test_view(self.test_cases_dir, "kebab-case")
		self.assert_rule_passes(view_file, self.rule_config, "NamePatternRule")


class TestNamePatternMultipleNodeTypes(BaseRuleTest):
	"""Test naming conventions applied to multiple node types."""

	def test_components_pascal_case_properties_camel_case(self):
		"""Test PascalCase for components and camelCase for properties."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "property"],
			convention="PascalCase",  # Default convention for components
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"min_length": 1
				},
				"property": {
					"convention": "camelCase",
					"min_length": 1
				}
			}
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_components_and_custom_methods_same_convention(self):
		"""Test applying same convention to components and custom methods."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component", "custom_method"], convention="camelCase",
			min_length=3
		)

		view_file = load_test_view(self.test_cases_dir, "camelCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_different_conventions_per_node_type(self):
		"""Test different naming conventions for different node types."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "custom_method", "message_handler"],
			convention="camelCase",  # Default convention
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"min_length": 1
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
		self.run_lint_on_file(view_file, rule_config)

		# Verify rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)


class TestNamePatternEdgeCases(BaseRuleTest):
	"""Test edge cases for naming pattern rules."""

	def test_min_length_validation(self):
		"""Test minimum length validation."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=5
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_max_length_validation(self):
		"""Test maximum length validation."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase", min_length=1,
			max_length=10
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

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
		self.run_lint_on_file(view_file, rule_config_with_numbers)
		errors_with_numbers = self.get_errors_for_rule("NamePatternRule")
		self.run_lint_on_file(view_file, rule_config_no_numbers)
		errors_no_numbers = self.get_errors_for_rule("NamePatternRule")

		self.assertIsInstance(errors_with_numbers, list)
		self.assertIsInstance(errors_no_numbers, list)

	def test_forbidden_names(self):
		"""Test forbidden component names."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase",
			forbidden_names=["Button", "Label", "Panel"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_custom_abbreviations(self):
		"""Test custom abbreviations handling."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase",
			allowed_abbreviations=["API", "HTTP", "XML"], auto_detect_abbreviations=False
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_skip_names(self):
		"""Test skipping certain names from validation."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"], convention="PascalCase",
			skip_names=["root", "main", "container"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_custom_pattern(self):
		"""Test custom regex pattern instead of predefined conventions."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["component"],
			custom_pattern=r"^(btn|lbl|pnl)[A-Z][a-zA-Z0-9]*$", min_length=4, max_length=25
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		# Verify the rule runs without crashing
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)


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
		self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_message_handler_naming(self):
		"""Test naming validation for message handlers."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["message_handler"], convention="snake_case", min_length=4,
			forbidden_names=["handler", "msg", "temp"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_property_naming_camel_case(self):
		"""Test naming validation for properties using camelCase."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["property"], convention="camelCase", min_length=2,
			forbidden_names=["temp", "tmp", "test", "data"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_event_handler_naming(self):
		"""Test naming validation for event handlers."""
		rule_config = get_test_config(
			"NamePatternRule", target_node_types=["event_handler"], convention="camelCase", min_length=4,
			skip_names=["onClick", "onFocus", "onBlur", "onLoad"]
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)

		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)


class TestStandardNamingConventions(BaseRuleTest):
	"""Test the standard conventions: PascalCase for components, camelCase for properties."""

	def test_standard_component_property_conventions(self):
		"""Test the standard: PascalCase components, camelCase properties."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "property"],
			convention="PascalCase",  # Default
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"min_length": 1,
					"allow_numbers": True
				},
				"property": {
					"convention": "camelCase",
					"min_length": 1,
					"allow_numbers": True,
					"skip_names": ["id", "x", "y", "z"]  # Common short property names
				}
			}
		)

		# Test with different view files
		test_cases = ["PascalCase", "camelCase"]
		for case in test_cases:
			with self.subTest(case=case):
				try:
					view_file = load_test_view(self.test_cases_dir, case)
					self.run_lint_on_file(view_file, rule_config)
					self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)
				except FileNotFoundError:
					self.skipTest(f"Test case {case} not found")

	def test_mixed_node_types_with_appropriate_conventions(self):
		"""Test multiple node types with their appropriate conventions."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "property", "custom_method", "event_handler"],
			convention="PascalCase",  # Default
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"min_length": 1
				},
				"property": {
					"convention": "camelCase",
					"min_length": 1
				},
				"custom_method": {
					"convention": "camelCase",
					"min_length": 3
				},
				"event_handler": {
					"convention": "camelCase",
					"min_length": 2,
					"skip_names": ["onClick", "onLoad", "onFocus", "onBlur"]
				}
			}
		)

		view_file = load_test_view(self.test_cases_dir, "PascalCase")
		self.run_lint_on_file(view_file, rule_config)
		self.assertIsInstance(self.get_errors_for_rule("NamePatternRule"), list)

	def test_pascal_case_components_camel_case_properties(self):
		"""Test that components follow PascalCase and properties follow camelCase."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "property"],
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"severity": "error"
				},
				"property": {
					"convention": "camelCase",
					"severity": "warning"
				}
			}
		)

		# Test with PascalCase view - components should pass, properties should fail
		view_file = load_test_view(self.test_cases_dir, "PascalCase")

		# Should have warnings for properties not following camelCase
		self.assert_rule_warnings(
			view_file, rule_config, "NamePatternRule",
			expected_warning_count=4,  # All custom properties are PascalCase
			warning_patterns=["doesn't follow camelCase", "property"]
		)

		# Should have no errors for components (they follow PascalCase)
		self.assert_rule_errors(
			view_file, rule_config, "NamePatternRule",
			expected_error_count=0
		)

	def test_camel_case_components_pascal_case_properties_fails(self):
		"""Test camelCase components with PascalCase properties - should produce errors and warnings."""
		rule_config = get_test_config(
			"NamePatternRule",
			target_node_types=["component", "property"],
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"severity": "error"
				},
				"property": {
					"convention": "camelCase",
					"severity": "warning"
				}
			}
		)

		# Test with camelCase view - components should fail PascalCase, properties should fail camelCase
		view_file = load_test_view(self.test_cases_dir, "camelCase")

		# Should have errors for components not following PascalCase
		self.assert_rule_errors(
			view_file, rule_config, "NamePatternRule",
			expected_error_count=1,  # The iconCamelCase component
			error_patterns=["doesn't follow PascalCase", "component"]
		)

		# Should have no warnings since properties are already camelCase
		# The camelCase view has camelCase properties, so they should pass the camelCase rule
		results = self.run_lint_on_file(view_file, rule_config)
		rule_warnings = results.warnings.get("NamePatternRule", [])
		self.assertEqual(len(rule_warnings), 0)

	def test_auto_derived_target_node_types(self):
		"""Test that target_node_types can be auto-derived from node_type_specific_rules."""
		rule_config = get_test_config(
			"NamePatternRule",
			# No explicit target_node_types provided
			node_type_specific_rules={
				"component": {
					"convention": "PascalCase",
					"severity": "warning"
				},
				"property": {
					"convention": "camelCase",
					"severity": "warning"
				}
			}
		)

		# Test with PascalCase view - should validate both components and properties
		view_file = load_test_view(self.test_cases_dir, "PascalCase")

		# Should have warnings for properties (they don't follow camelCase)
		self.assert_rule_warnings(
			view_file, rule_config, "NamePatternRule",
			expected_warning_count=4,  # All properties are PascalCase instead of camelCase
			warning_patterns=["doesn't follow camelCase", "property"]
		)

		# Should have no errors since severity is set to warning
		self.assert_rule_errors(
			view_file, rule_config, "NamePatternRule",
			expected_error_count=0
		)


if __name__ == "__main__":
	unittest.main()
