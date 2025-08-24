"""
Configuration-driven test framework for ignition-lint.
This module allows defining test cases in JSON configuration files
and automatically generates and runs the appropriate tests.
"""

import unittest
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Add the src directory to the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ignition_lint.linter import LintEngine
from ignition_lint.rules import RULES_MAP
from ignition_lint.common.flatten_json import flatten_file


@dataclass
class TestExpectation:
	"""Represents expected results for a test case."""
	rule_name: str
	error_count: int
	error_patterns: List[str] = None
	should_pass: bool = None

	def __post_init__(self):
		if self.error_patterns is None:
			self.error_patterns = []
		if self.should_pass is None:
			self.should_pass = self.error_count == 0


@dataclass
class ConfigurableTestCase:
	"""Represents a test case defined in configuration."""
	name: str
	description: str
	view_file: str
	rule_config: Dict[str, Any]
	expectations: List[TestExpectation]
	tags: List[str] = None
	skip: bool = False
	skip_reason: str = ""

	def __post_init__(self):
		if self.tags is None:
			self.tags = []


class ConfigurableTestFramework:
	"""Framework for running tests defined in configuration files."""

	def __init__(self, config_dir: Path = None, test_cases_dir: Path = None):
		"""
		Initialize the framework.
		
		Args:
			config_dir: Directory containing test configuration files
			test_cases_dir: Directory containing test case view.json files
		"""
		# Get the tests directory (parent of fixtures)
		tests_dir = Path(__file__).parent.parent

		if config_dir is None:
			config_dir = tests_dir / "configs"
		if test_cases_dir is None:
			test_cases_dir = tests_dir / "cases"

		self.config_dir = config_dir
		self.test_cases_dir = test_cases_dir
		self.test_cases: List[ConfigurableTestCase] = []

	def load_test_configurations(self) -> List[ConfigurableTestCase]:
		"""
		Load test configurations from JSON files.
		
		Returns:
			List of configured test cases
		"""
		test_cases = []

		if not self.config_dir.exists():
			return test_cases

		for config_file in self.config_dir.glob("*.json"):
			try:
				with open(config_file, 'r') as f:
					config_data = json.load(f)

				# Parse test cases from configuration
				for case_data in config_data.get('test_cases', []):
					expectations = []
					for exp_data in case_data.get('expectations', []):
						expectations.append(
							TestExpectation(
								rule_name=exp_data['rule_name'],
								error_count=exp_data.get('error_count', 0),
								error_patterns=exp_data.get('error_patterns', []),
								should_pass=exp_data.get('should_pass')
							)
						)

					test_case = ConfigurableTestCase(
						name=case_data['name'], description=case_data.get('description', ''),
						view_file=case_data['view_file'], rule_config=case_data['rule_config'],
						expectations=expectations, tags=case_data.get('tags', []),
						skip=case_data.get('skip', False),
						skip_reason=case_data.get('skip_reason', '')
					)
					test_cases.append(test_case)

			except Exception as e:
				print(f"Error loading config file {config_file}: {e}")

		return test_cases

	def run_single_test(self, test_case: ConfigurableTestCase) -> Dict[str, Any]:
		"""
		Run a single test case and return results.
		
		Args:
			test_case: The test case to run
			
		Returns:
			Dictionary containing test results
		"""
		if test_case.skip:
			return {
				'name': test_case.name,
				'status': 'skipped',
				'reason': test_case.skip_reason,
				'errors': [],
				'expectations_met': True
			}

		# Resolve view file path
		view_file_path = self.test_cases_dir / test_case.view_file
		if not view_file_path.exists():
			return {
				'name': test_case.name,
				'status': 'error',
				'reason': f"View file not found: {view_file_path}",
				'errors': [],
				'expectations_met': False
			}

		try:
			# Create rules from config
			rules = []
			for rule_name, rule_config in test_case.rule_config.items():
				if rule_name.startswith("_") or not isinstance(rule_config, dict):
					continue

				if not rule_config.get('enabled', True):
					continue

				if rule_name not in RULES_MAP:
					continue

				rule_class = RULES_MAP[rule_name]
				kwargs = rule_config.get('kwargs', {})

				try:
					rules.append(rule_class(**kwargs))
				except Exception as e:
					print(f"Error creating rule {rule_name}: {e}")
					continue

			# Run linting
			lint_engine = LintEngine(rules)
			flattened_json = flatten_file(view_file_path)
			actual_errors = lint_engine.process(flattened_json)

			# Check expectations
			expectations_met = True
			expectation_details = []

			for expectation in test_case.expectations:
				rule_errors = actual_errors.get(expectation.rule_name, [])
				actual_count = len(rule_errors)

				count_match = actual_count == expectation.error_count
				pass_match = (actual_count == 0) == expectation.should_pass

				pattern_matches = []
				if expectation.error_patterns:
					for pattern in expectation.error_patterns:
						matches = [error for error in rule_errors if pattern in error]
						pattern_matches.append({
							'pattern': pattern,
							'matches': len(matches),
							'found': len(matches) > 0
						})

				expectation_met = count_match and pass_match
				if expectation.error_patterns:
					expectation_met = expectation_met and all(pm['found'] for pm in pattern_matches)

				expectations_met = expectations_met and expectation_met

				expectation_details.append({
					'rule_name': expectation.rule_name,
					'expected_count': expectation.error_count,
					'actual_count': actual_count,
					'should_pass': expectation.should_pass,
					'count_match': count_match,
					'pass_match': pass_match,
					'pattern_matches': pattern_matches,
					'met': expectation_met
				})

			return {
				'name': test_case.name,
				'status': 'passed' if expectations_met else 'failed',
				'reason': '',
				'errors': actual_errors,
				'expectations_met': expectations_met,
				'expectation_details': expectation_details
			}

		except Exception as e:
			return {
				'name': test_case.name,
				'status': 'error',
				'reason': f"Test execution failed: {str(e)}",
				'errors': [],
				'expectations_met': False
			}

	def run_all_tests(self, tags: List[str] = None) -> Dict[str, Any]:
		"""
		Run all loaded test cases, optionally filtered by tags.
		
		Args:
			tags: Optional list of tags to filter tests
			
		Returns:
			Dictionary containing overall test results
		"""
		test_cases = self.load_test_configurations()

		# Filter by tags if specified
		if tags:
			test_cases = [tc for tc in test_cases if any(tag in tc.tags for tag in tags)]

		results = []
		passed = 0
		failed = 0
		skipped = 0
		errors = 0

		for test_case in test_cases:
			result = self.run_single_test(test_case)
			results.append(result)

			if result['status'] == 'passed':
				passed += 1
			elif result['status'] == 'failed':
				failed += 1
			elif result['status'] == 'skipped':
				skipped += 1
			else:  # error
				errors += 1

		return {
			'total': len(test_cases),
			'passed': passed,
			'failed': failed,
			'skipped': skipped,
			'errors': errors,
			'results': results
		}

	def generate_test_config_template(self, rule_name: str, output_file: str = None):
		"""
		Generate a template configuration file for a specific rule.
		
		Args:
			rule_name: Name of the rule to generate config for
			output_file: Optional output file path
		"""
		if rule_name not in RULES_MAP:
			raise ValueError(f"Unknown rule: {rule_name}")

		template = {
			"test_suite_name": f"{rule_name} Tests",
			"description": f"Test cases for the {rule_name} rule",
			"test_cases": [
				{
					"name": f"{rule_name}_positive_case",
					"description": "Test case that should pass the rule",
					"view_file": "cases/PascalCase/view.json",  # Example
					"rule_config": {
						rule_name: {
							"enabled": True,
							"kwargs": {}  # Add rule-specific kwargs here
						}
					},
					"expectations": [{
						"rule_name": rule_name,
						"error_count": 0,
						"should_pass": True,
						"error_patterns": []
					}],
					"tags": [rule_name.lower(), "positive"],
					"skip": False
				},
				{
					"name": f"{rule_name}_negative_case",
					"description": "Test case that should fail the rule",
					"view_file": "cases/camelCase/view.json",  # Example
					"rule_config": {
						rule_name: {
							"enabled": True,
							"kwargs": {}  # Add rule-specific kwargs here
						}
					},
					"expectations": [{
						"rule_name": rule_name,
						"error_count": 1,  # Adjust based on expected failures
						"should_pass": False,
						"error_patterns": ["doesn't follow"]  # Example pattern
					}],
					"tags": [rule_name.lower(), "negative"],
					"skip": False
				}
			]
		}

		if output_file is None:
			output_file = f"{rule_name.lower()}_tests.json"

		output_path = self.config_dir / output_file
		output_path.parent.mkdir(parents=True, exist_ok=True)

		with open(output_path, 'w') as f:
			json.dump(template, f, indent=2)

		print(f"Generated template configuration: {output_path}")


class ConfigurableTestRunner(unittest.TestCase):
	"""Unit test class that runs configuration-driven tests."""

	def setUp(self):
		"""Set up the test framework."""
		self.framework = ConfigurableTestFramework()

	def test_run_configured_tests(self):
		"""Run all configured test cases."""
		results = self.framework.run_all_tests()

		# Print detailed results
		print(f"\nTest Results Summary:")
		print(f"Total: {results['total']}")
		print(f"Passed: {results['passed']}")
		print(f"Failed: {results['failed']}")
		print(f"Skipped: {results['skipped']}")
		print(f"Errors: {results['errors']}")

		# Print details for failed tests
		for result in results['results']:
			if result['status'] == 'failed':
				print(f"\nFAILED: {result['name']}")
				if 'expectation_details' in result:
					for detail in result['expectation_details']:
						if not detail['met']:
							print(f"  Rule: {detail['rule_name']}")
							print(
								f"    Expected count: {detail['expected_count']}, Got: {detail['actual_count']}"
							)
							print(f"    Should pass: {detail['should_pass']}")
			elif result['status'] == 'error':
				print(f"\nERROR: {result['name']} - {result['reason']}")

		# Assert that all tests passed (no failures or errors)
		self.assertEqual(results['failed'], 0, f"Some tests failed. See details above.")
		self.assertEqual(results['errors'], 0, f"Some tests had errors. See details above.")


def create_sample_test_configs():
	"""Create sample test configuration files for each rule."""
	framework = ConfigurableTestFramework()

	# Ensure config directory exists
	framework.config_dir.mkdir(parents=True, exist_ok=True)

	# Component naming rule tests
	component_name_config = {
		"test_suite_name": "NamePatternRule Tests",
		"description": "Test cases for component naming conventions",
		"test_cases": [{
			"name": "pascal_case_positive",
			"description": "PascalCase view should pass PascalCase rule",
			"view_file": "PascalCase/view.json",
			"rule_config": {
				"NamePatternRule": {
					"enabled": True,
					"kwargs": {
						"convention": "PascalCase",
						"allow_numbers": True,
						"min_length": 1
					}
				}
			},
			"expectations": [{
				"rule_name": "NamePatternRule",
				"error_count": 0,
				"should_pass": True
			}],
			"tags": ["component_naming", "pascal_case", "positive"]
		}, {
			"name": "pascal_case_negative",
			"description": "camelCase view should fail PascalCase rule",
			"view_file": "camelCase/view.json",
			"rule_config": {
				"NamePatternRule": {
					"enabled": True,
					"kwargs": {
						"convention": "PascalCase",
						"allow_numbers": True,
						"min_length": 1
					}
				}
			},
			"expectations": [{
				"rule_name": "NamePatternRule",
				"error_count": 1,
				"should_pass": False,
				"error_patterns": ["doesn't follow"]
			}],
			"tags": ["component_naming", "pascal_case", "negative"]
		}, {
			"name": "camel_case_positive",
			"description": "camelCase view should pass camelCase rule",
			"view_file": "camelCase/view.json",
			"rule_config": {
				"NamePatternRule": {
					"enabled": True,
					"kwargs": {
						"convention": "camelCase",
						"allow_numbers": True,
						"min_length": 1
					}
				}
			},
			"expectations": [{
				"rule_name": "NamePatternRule",
				"error_count": 0,
				"should_pass": True
			}],
			"tags": ["component_naming", "camel_case", "positive"]
		}, {
			"name": "snake_case_positive",
			"description": "snake_case view should pass snake_case rule",
			"view_file": "snake_case/view.json",
			"rule_config": {
				"NamePatternRule": {
					"enabled": True,
					"kwargs": {
						"convention": "snake_case",
						"allow_numbers": True,
						"min_length": 1
					}
				}
			},
			"expectations": [{
				"rule_name": "NamePatternRule",
				"error_count": 0,
				"should_pass": True
			}],
			"tags": ["component_naming", "snake_case", "positive"]
		}, {
			"name": "inconsistent_case_negative",
			"description": "inconsistentCase view should fail any naming rule",
			"view_file": "inconsistentCase/view.json",
			"rule_config": {
				"NamePatternRule": {
					"enabled": True,
					"kwargs": {
						"convention": "PascalCase",
						"allow_numbers": True,
						"min_length": 1
					}
				}
			},
			"expectations": [{
				"rule_name": "NamePatternRule",
				"error_count": 1,
				"should_pass": False
			}],
			"tags": ["component_naming", "inconsistent", "negative"]
		}]
	}

	# Polling interval rule tests
	polling_interval_config = {
		"test_suite_name": "PollingIntervalRule Tests",
		"description": "Test cases for polling interval validation",
		"test_cases": [{
			"name": "expression_bindings_check",
			"description": "Check expression bindings for polling intervals",
			"view_file": "ExpressionBindings/view.json",
			"rule_config": {
				"PollingIntervalRule": {
					"enabled": True,
					"kwargs": {
						"minimum_interval": 10000
					}
				}
			},
			"expectations": [{
				"rule_name": "PollingIntervalRule",
				"error_count": 0,
				"should_pass": True
			}],
			"tags": ["polling", "expressions", "bindings"]
		}]
	}

	# Script linting tests
	script_linting_config = {
		"test_suite_name": "PylintScriptRule Tests",
		"description": "Test cases for script linting with pylint",
		"test_cases": [{
			"name": "basic_script_check",
			"description": "Basic script linting check",
			"view_file": "PascalCase/view.json",
			"rule_config": {
				"PylintScriptRule": {
					"enabled": True,
					"kwargs": {}
				}
			},
			"expectations": [{
				"rule_name": "PylintScriptRule",
				"error_count": 0,
				"should_pass": True
			}],
			"tags": ["scripts", "pylint", "basic"],
			"skip": False,
			"skip_reason": ""
		}]
	}

	# Write configuration files
	configs = [("component_naming_tests.json", component_name_config),
			("polling_interval_tests.json", polling_interval_config),
			("script_linting_tests.json", script_linting_config)]

	for filename, config in configs:
		config_path = framework.config_dir / filename
		with open(config_path, 'w') as f:
			json.dump(config, f, indent=2)
		print(f"Created configuration file: {config_path}")


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Configuration-driven test framework for ignition-lint")
	parser.add_argument("--create-configs", action="store_true", help="Create sample test configuration files")
	parser.add_argument("--run-tests", action="store_true", help="Run all configured tests")
	parser.add_argument("--tags", nargs="+", help="Filter tests by tags")
	parser.add_argument("--generate-template", help="Generate a template config for a specific rule")

	args = parser.parse_args()

	if args.create_configs:
		create_sample_test_configs()
	elif args.generate_template:
		framework = ConfigurableTestFramework()
		framework.generate_test_config_template(args.generate_template)
	elif args.run_tests:
		framework = ConfigurableTestFramework()
		results = framework.run_all_tests(tags=args.tags)

		print(f"\nTest Results Summary:")
		print(f"Total: {results['total']}")
		print(f"Passed: {results['passed']}")
		print(f"Failed: {results['failed']}")
		print(f"Skipped: {results['skipped']}")
		print(f"Errors: {results['errors']}")

		if results['failed'] > 0 or results['errors'] > 0:
			print(f"\nDetailed Results:")
			for result in results['results']:
				if result['status'] in ['failed', 'error']:
					print(f"\n{result['status'].upper()}: {result['name']}")
					if result['reason']:
						print(f"  Reason: {result['reason']}")
					if 'expectation_details' in result:
						for detail in result['expectation_details']:
							if not detail['met']:
								print(f"  Rule {detail['rule_name']}:")
								print(
									f"    Expected {detail['expected_count']} errors, got {detail['actual_count']}"
								)

		sys.exit(0 if results['failed'] == 0 and results['errors'] == 0 else 1)
	else:
		# Run as unittest - use modern approach
		loader = unittest.TestLoader()
		suite = unittest.TestSuite()
		suite.addTests(loader.loadTestsFromTestCase(ConfigurableTestRunner))
		runner = unittest.TextTestRunner(verbosity=2)
		result = runner.run(suite)
		sys.exit(0 if result.wasSuccessful() else 1)
