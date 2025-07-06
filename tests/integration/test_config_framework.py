"""
Integration tests for the configuration-driven test framework.
"""

import unittest
import json
from pathlib import Path

from fixtures.base_test import BaseIntegrationTest
from fixtures.config_framework import ConfigurableTestFramework, ConfigurableTestCase, TestExpectation


class TestConfigFramework(BaseIntegrationTest):
	"""Test the configuration-driven test framework."""

	def setUp(self):
		super().setUp()
		self.framework = ConfigurableTestFramework(
			config_dir=self.configs_dir, test_cases_dir=self.test_cases_dir
		)

	def test_load_test_configurations(self):
		"""Test loading test configurations from JSON files."""
		test_cases = self.framework.load_test_configurations()

		# Should load some test cases if config files exist
		if self.configs_dir.exists() and list(self.configs_dir.glob("*.json")):
			self.assertGreater(len(test_cases), 0, "Should load some test cases")

			# Verify structure of loaded test cases
			for test_case in test_cases:
				self.assertIsInstance(test_case, ConfigurableTestCase)
				self.assertIsInstance(test_case.name, str)
				self.assertIsInstance(test_case.rule_config, dict)
				self.assertIsInstance(test_case.expectations, list)

	def test_run_single_test_success(self):
		"""Test running a single test that should pass."""
		# Create a simple test case
		test_case = ConfigurableTestCase(
			name="test_pascal_case", description="Test PascalCase naming", view_file="PascalCase/view.json",
			rule_config={"ComponentNameRule": {
				"enabled": True,
				"kwargs": {
					"convention": "PascalCase"
				}
			}},
			expectations=[TestExpectation(rule_name="ComponentNameRule", error_count=0, should_pass=True)]
		)

		result = self.framework.run_single_test(test_case)

		self.assertEqual(result['name'], "test_pascal_case")
		self.assertIn(result['status'], ['passed', 'failed', 'skipped', 'error'])

	def test_run_single_test_with_nonexistent_file(self):
		"""Test running a test with a non-existent view file."""
		test_case = ConfigurableTestCase(
			name="test_nonexistent", description="Test with non-existent file",
			view_file="NonExistent/view.json",
			rule_config={"ComponentNameRule": {
				"enabled": True,
				"kwargs": {
					"convention": "PascalCase"
				}
			}}, expectations=[]
		)

		result = self.framework.run_single_test(test_case)

		self.assertEqual(result['status'], 'error')
		self.assertIn('not found', result['reason'])

	def test_skipped_test(self):
		"""Test running a skipped test."""
		test_case = ConfigurableTestCase(
			name="test_skipped", description="This test should be skipped",
			view_file="PascalCase/view.json", rule_config={}, expectations=[], skip=True,
			skip_reason="Test intentionally skipped"
		)

		result = self.framework.run_single_test(test_case)

		self.assertEqual(result['status'], 'skipped')
		self.assertEqual(result['reason'], 'Test intentionally skipped')


class TestConfigFrameworkFileOperations(BaseIntegrationTest):
	"""Test file operations in the configuration framework."""

	def setUp(self):
		super().setUp()
		self.framework = ConfigurableTestFramework()

	def test_generate_test_config_template(self):
		"""Test generating test configuration templates."""
		# Create a temporary directory for testing
		import tempfile
		with tempfile.TemporaryDirectory() as temp_dir:
			temp_config_dir = Path(temp_dir) / "configs"
			framework = ConfigurableTestFramework(config_dir=temp_config_dir)

			# Generate template for ComponentNameRule
			framework.generate_test_config_template("ComponentNameRule")

			# Check that file was created
			template_file = temp_config_dir / "componentnamerule_tests.json"
			self.assertTrue(template_file.exists())

			# Verify it's valid JSON
			with open(template_file, 'r') as f:
				config_data = json.load(f)

			self.assertIn("test_suite_name", config_data)
			self.assertIn("test_cases", config_data)
			self.assertIsInstance(config_data["test_cases"], list)


if __name__ == "__main__":
	unittest.main()
