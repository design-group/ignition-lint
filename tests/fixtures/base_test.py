"""
Base test classes providing common functionality for ignition-lint tests.
"""

import unittest
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the src directory to the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from ignition_lint.linter import LintEngine
from ignition_lint.rules import RULES_MAP
from ignition_lint.common.flatten_json import flatten_file


class BaseRuleTest(unittest.TestCase):
	"""Base class for testing individual linting rules."""

	def setUp(self):
		"""Set up test fixtures."""
		# Get the tests directory (two levels up from fixtures)
		tests_dir = Path(__file__).parent.parent
		self.test_cases_dir = tests_dir / "cases"
		self.configs_dir = tests_dir / "configs"

	def create_lint_engine(self, rule_configs: Dict[str, Dict[str, Any]]) -> LintEngine:
		"""
		Create a lint engine with the specified rules.
		
		Args:
			rule_configs: Dictionary mapping rule names to their configurations
			
		Returns:
			Configured LintEngine instance
		"""
		rules = []
		for rule_name, config in rule_configs.items():
			if rule_name not in RULES_MAP:
				self.fail(f"Unknown rule: {rule_name}")

			rule_class = RULES_MAP[rule_name]
			kwargs = config.get('kwargs', {})

			try:
				# Use create_from_config to enable preprocessing
				rules.append(rule_class.create_from_config(kwargs))
			except Exception as e:
				self.fail(f"Failed to create rule {rule_name}: {e}")

		return LintEngine(rules)

	def run_lint_on_file(self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
		"""
		Run linting on a view file with the given rule configuration.
		
		Args:
			view_file: Path to the view.json file
			rule_configs: Rule configurations
			
		Returns:
			Dictionary of errors found by rule (combined warnings and errors for backward compatibility)
		"""
		if not view_file.exists():
			self.skipTest(f"View file not found: {view_file}")

		lint_engine = self.create_lint_engine(rule_configs)
		flattened_json = flatten_file(view_file)
		lint_results = lint_engine.process(flattened_json)

		# Combine warnings and errors for backward compatibility
		combined_results = {}
		combined_results.update(lint_results.warnings)
		combined_results.update(lint_results.errors)

		return combined_results

	def run_lint_on_file_detailed(self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]]):
		"""
		Run linting on a view file and return detailed results with warnings and errors separated.
		
		Args:
			view_file: Path to the view.json file
			rule_configs: Rule configurations
			
		Returns:
			LintResults object with separate warnings and errors
		"""
		if not view_file.exists():
			self.skipTest(f"View file not found: {view_file}")

		lint_engine = self.create_lint_engine(rule_configs)
		flattened_json = flatten_file(view_file)
		return lint_engine.process(flattened_json)

	def assert_rule_passes(self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str):
		"""Assert that a rule passes (no errors) for a given view file."""
		errors = self.run_lint_on_file(view_file, rule_configs)
		rule_errors = errors.get(rule_name, [])
		self.assertEqual(rule_errors, [], f"Rule {rule_name} should pass but found errors: {rule_errors}")

	def assert_rule_fails(
		self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str,
		expected_error_count: int = None
	):
		"""Assert that a rule fails (has errors) for a given view file."""
		errors = self.run_lint_on_file(view_file, rule_configs)
		rule_errors = errors.get(rule_name, [])

		self.assertGreater(len(rule_errors), 0, f"Rule {rule_name} should fail but found no errors")

		if expected_error_count is not None:
			self.assertEqual(
				len(rule_errors), expected_error_count,
				f"Rule {rule_name} should have {expected_error_count} errors but found {len(rule_errors)}: {rule_errors}"
			)

	def assert_error_contains(
		self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str, error_pattern: str
	):
		"""Assert that rule errors contain a specific pattern."""
		errors = self.run_lint_on_file(view_file, rule_configs)
		rule_errors = errors.get(rule_name, [])

		matching_errors = [error for error in rule_errors if error_pattern in error]
		self.assertGreater(
			len(matching_errors), 0,
			f"Rule {rule_name} errors should contain '{error_pattern}'. Found errors: {rule_errors}"
		)

	# New detailed assertion methods for warnings and errors

	def assert_rule_warnings(
		self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str,
		expected_warning_count: int, warning_patterns: list = None
	):
		"""Assert that a rule produces the expected number of warnings with optional pattern matching."""
		results = self.run_lint_on_file_detailed(view_file, rule_configs)
		rule_warnings = results.warnings.get(rule_name, [])

		self.assertEqual(
			len(rule_warnings), expected_warning_count,
			f"Rule {rule_name} should produce {expected_warning_count} warnings but produced {len(rule_warnings)}: {rule_warnings}"
		)

		if warning_patterns:
			for pattern in warning_patterns:
				matching_warnings = [warning for warning in rule_warnings if pattern in warning]
				self.assertGreater(
					len(matching_warnings), 0,
					f"Rule {rule_name} warnings should contain '{pattern}'. Found warnings: {rule_warnings}"
				)

	def assert_rule_errors(
		self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str,
		expected_error_count: int, error_patterns: list = None
	):
		"""Assert that a rule produces the expected number of errors with optional pattern matching."""
		results = self.run_lint_on_file_detailed(view_file, rule_configs)
		rule_errors = results.errors.get(rule_name, [])

		self.assertEqual(
			len(rule_errors), expected_error_count,
			f"Rule {rule_name} should produce {expected_error_count} errors but produced {len(rule_errors)}: {rule_errors}"
		)

		if error_patterns:
			for pattern in error_patterns:
				matching_errors = [error for error in rule_errors if pattern in error]
				self.assertGreater(
					len(matching_errors), 0,
					f"Rule {rule_name} errors should contain '{pattern}'. Found errors: {rule_errors}"
				)

	def assert_rule_passes_completely(
		self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str
	):
		"""Assert that a rule passes completely (no warnings or errors)."""
		results = self.run_lint_on_file_detailed(view_file, rule_configs)
		rule_warnings = results.warnings.get(rule_name, [])
		rule_errors = results.errors.get(rule_name, [])

		self.assertEqual(
			rule_warnings, [], f"Rule {rule_name} should have no warnings but found: {rule_warnings}"
		)
		self.assertEqual(rule_errors, [], f"Rule {rule_name} should have no errors but found: {rule_errors}")

	def assert_rule_summary(
		self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]], rule_name: str,
		expected_warnings: int = 0, expected_errors: int = 0
	):
		"""Assert the total warnings and errors count for a rule."""
		results = self.run_lint_on_file_detailed(view_file, rule_configs)
		rule_warnings = results.warnings.get(rule_name, [])
		rule_errors = results.errors.get(rule_name, [])

		self.assertEqual(
			len(rule_warnings), expected_warnings,
			f"Rule {rule_name} should have {expected_warnings} warnings but found {len(rule_warnings)}: {rule_warnings}"
		)
		self.assertEqual(
			len(rule_errors), expected_errors,
			f"Rule {rule_name} should have {expected_errors} errors but found {len(rule_errors)}: {rule_errors}"
		)


class BaseIntegrationTest(unittest.TestCase):
	"""Base class for integration tests involving multiple components."""

	def setUp(self):
		"""Set up test fixtures."""
		# Get the tests directory (two levels up from fixtures)
		tests_dir = Path(__file__).parent.parent
		self.test_cases_dir = tests_dir / "cases"
		self.configs_dir = tests_dir / "configs"

	def run_multiple_rules(self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
		"""
		Run multiple rules on a view file.
		
		Args:
			view_file: Path to the view.json file
			rule_configs: Dictionary of rule configurations
			
		Returns:
			Dictionary of errors by rule name (combined warnings and errors for backward compatibility)
		"""
		if not view_file.exists():
			self.skipTest(f"View file not found: {view_file}")

		# Create rules
		rules = []
		for rule_name, config in rule_configs.items():
			if rule_name not in RULES_MAP:
				continue

			rule_class = RULES_MAP[rule_name]
			kwargs = config.get('kwargs', {})

			try:
				# Use create_from_config to enable preprocessing
				rules.append(rule_class.create_from_config(kwargs))
			except Exception as e:
				self.fail(f"Failed to create rule {rule_name}: {e}")

		# Run linting
		lint_engine = LintEngine(rules)
		flattened_json = flatten_file(view_file)
		lint_results = lint_engine.process(flattened_json)

		# Combine warnings and errors for backward compatibility
		combined_results = {}
		combined_results.update(lint_results.warnings)
		combined_results.update(lint_results.errors)

		return combined_results

	def run_multiple_rules_detailed(self, view_file: Path, rule_configs: Dict[str, Dict[str, Any]]):
		"""
		Run multiple rules on a view file and return detailed results.
		
		Args:
			view_file: Path to the view.json file
			rule_configs: Dictionary of rule configurations
			
		Returns:
			LintResults object with separate warnings and errors
		"""
		if not view_file.exists():
			self.skipTest(f"View file not found: {view_file}")

		# Create rules
		rules = []
		for rule_name, config in rule_configs.items():
			if rule_name not in RULES_MAP:
				continue

			rule_class = RULES_MAP[rule_name]
			kwargs = config.get('kwargs', {})

			try:
				# Use create_from_config to enable preprocessing
				rules.append(rule_class.create_from_config(kwargs))
			except Exception as e:
				self.fail(f"Failed to create rule {rule_name}: {e}")

		# Run linting
		lint_engine = LintEngine(rules)
		flattened_json = flatten_file(view_file)
		return lint_engine.process(flattened_json)

	def assert_total_errors(self, errors: Dict[str, List[str]], expected_total: int):
		"""Assert the total number of errors across all rules."""
		total_errors = sum(len(rule_errors) for rule_errors in errors.values())
		self.assertEqual(
			total_errors, expected_total,
			f"Expected {expected_total} total errors but found {total_errors}. Errors: {errors}"
		)
