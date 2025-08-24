#!/usr/bin/env python3
"""
Modular test runner script for ignition-lint.
This script provides a simple command-line interface for running organized tests.
"""

import argparse
import os
import sys
import unittest
from pathlib import Path

# Add the src directory to the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fixtures.config_framework import ConfigurableTestFramework, create_sample_test_configs


def discover_and_run_unit_tests(test_pattern=None, verbosity=2):
	"""Discover and run unit tests from the unit/ directory."""
	test_dir = Path(__file__).parent / "unit"

	if not test_dir.exists():
		print(f"Unit tests directory not found: {test_dir}")
		return False

	# Discover tests
	loader = unittest.TestLoader()
	if test_pattern:
		suite = loader.discover(str(test_dir), pattern=test_pattern)
	else:
		suite = loader.discover(str(test_dir), pattern="test_*.py")

	# Run tests
	runner = unittest.TextTestRunner(verbosity=verbosity)
	result = runner.run(suite)

	return result.wasSuccessful()


def discover_and_run_integration_tests(test_pattern=None, verbosity=2):
	"""Discover and run integration tests from the integration/ directory."""
	test_dir = Path(__file__).parent / "integration"

	if not test_dir.exists():
		print(f"Integration tests directory not found: {test_dir}")
		return False

	# Discover tests
	loader = unittest.TestLoader()
	if test_pattern:
		suite = loader.discover(str(test_dir), pattern=test_pattern)
	else:
		suite = loader.discover(str(test_dir), pattern="test_*.py")

	# Run tests
	runner = unittest.TextTestRunner(verbosity=verbosity)
	result = runner.run(suite)

	return result.wasSuccessful()


def run_specific_test_file(test_file, verbosity=2):
	"""Run tests from a specific test file."""
	test_path = Path(__file__).parent / test_file

	if not test_path.exists():
		# Try with .py extension
		test_path = Path(str(test_path) + ".py")
		if not test_path.exists():
			print(f"Test file not found: {test_file}")
			return False

	# Load and run the specific test module
	loader = unittest.TestLoader()

	# Convert path to module name
	relative_path = test_path.relative_to(Path(__file__).parent)
	module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')

	try:
		suite = loader.loadTestsFromName(module_name)
		runner = unittest.TextTestRunner(verbosity=verbosity)
		result = runner.run(suite)
		return result.wasSuccessful()
	except Exception as e:
		print(f"Error loading test module {module_name}: {e}")
		return False


def run_config_tests(tags=None):
	"""Run configuration-driven tests."""
	framework = ConfigurableTestFramework()
	results = framework.run_all_tests(tags=tags)

	print(f"\nConfiguration Test Results:")
	print(f"Total: {results['total']}")
	print(f"Passed: {results['passed']}")
	print(f"Failed: {results['failed']}")
	print(f"Skipped: {results['skipped']}")
	print(f"Errors: {results['errors']}")

	# Print detailed results for failures
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
							# Handle both old and new format
							if 'expected_count' in detail:
								print(
									f"    Expected {detail['expected_count']} errors, got {detail['actual_count']}"
								)
							else:
								print(
									f"    Expected {detail['expected_warnings']} warnings, got {detail['actual_warnings']}"
								)
								print(
									f"    Expected {detail['expected_errors']} errors, got {detail['actual_errors']}"
								)
							# Handle pattern matches for both old and new format
							if 'pattern_matches' in detail and detail['pattern_matches']:
								for pm in detail['pattern_matches']:
									if not pm['found']:
										print(
											f"    Missing pattern: '{pm['pattern']}'"
										)
							elif 'error_pattern_matches' in detail or 'warning_pattern_matches' in detail:
								# New format with separate error and warning patterns
								for pm in detail.get('error_pattern_matches', []):
									if not pm['found']:
										print(
											f"    Missing error pattern: '{pm['pattern']}'"
										)
								for pm in detail.get('warning_pattern_matches', []):
									if not pm['found']:
										print(
											f"    Missing warning pattern: '{pm['pattern']}'"
										)

	return results['failed'] == 0 and results['errors'] == 0


def list_available_tests():
	"""List all available test modules and categories."""
	print("Available Test Categories:\n")

	base_dir = Path(__file__).parent

	# List unit tests
	unit_dir = base_dir / "unit"
	if unit_dir.exists():
		print("1. Unit Tests:")
		for test_file in sorted(unit_dir.glob("test_*.py")):
			print(f"   - {test_file.stem}")

	# List integration tests
	integration_dir = base_dir / "integration"
	if integration_dir.exists():
		print("\n2. Integration Tests:")
		for test_file in sorted(integration_dir.glob("test_*.py")):
			print(f"   - {test_file.stem}")

	# List configuration-driven tests
	print("\n3. Configuration-driven Tests:")
	framework = ConfigurableTestFramework()
	test_cases = framework.load_test_configurations()

	if test_cases:
		# Group by tags
		by_tags = {}
		for tc in test_cases:
			for tag in tc.tags:
				if tag not in by_tags:
					by_tags[tag] = []
				by_tags[tag].append(tc.name)

		for tag, cases in by_tags.items():
			print(f"   Tag '{tag}':")
			for case in cases:
				print(f"     - {case}")
	else:
		print("   No configuration files found. Run with --create-configs first.")

	# List test case directories
	print("\n4. Test Cases Directory Structure:")
	cases_dir = base_dir / "cases"
	if cases_dir.exists():
		for case_dir in sorted(cases_dir.iterdir()):
			if case_dir.is_dir():
				view_files = list(case_dir.glob("**/view.json"))
				print(f"   {case_dir.name}/")
				for vf in view_files:
					print(f"     - {vf.relative_to(cases_dir)}")


def setup_test_environment():
	"""Set up the test environment by creating necessary directories and files."""
	base_dir = Path(__file__).parent

	# Create directories
	dirs_to_create = [
		base_dir / "unit",
		base_dir / "integration",
		base_dir / "fixtures",
		base_dir / "configs",
		base_dir / "results",
		base_dir / "cases"  # In case it doesn't exist
	]

	for dir_path in dirs_to_create:
		dir_path.mkdir(parents=True, exist_ok=True)
		print(f"Created directory: {dir_path}")

	# Create __init__.py files for Python packages
	init_files = [
		base_dir / "__init__.py", base_dir / "unit" / "__init__.py", base_dir / "integration" / "__init__.py",
		base_dir / "fixtures" / "__init__.py"
	]

	for init_file in init_files:
		if not init_file.exists():
			init_file.write_text('"""Test package module."""\n')
			print(f"Created: {init_file}")

	# Create sample configurations
	try:
		create_sample_test_configs()
	except Exception as e:
		print(f"Warning: Could not create sample configs: {e}")

	print("\nTest environment setup complete!")
	print("You can now run tests with:")
	print("  python test_runner.py --run-unit")
	print("  python test_runner.py --run-integration")
	print("  python test_runner.py --run-config")


def run_test_by_name(test_name, verbosity=2):
	"""Run a specific test by name (supports partial matching)."""
	base_dir = Path(__file__).parent

	# Search in unit tests
	unit_dir = base_dir / "unit"
	if unit_dir.exists():
		for test_file in unit_dir.glob("test_*.py"):
			if test_name.lower() in test_file.stem.lower():
				print(f"Running unit test: {test_file.stem}")
				return run_specific_test_file(f"unit/{test_file.name}", verbosity)

	# Search in integration tests
	integration_dir = base_dir / "integration"
	if integration_dir.exists():
		for test_file in integration_dir.glob("test_*.py"):
			if test_name.lower() in test_file.stem.lower():
				print(f"Running integration test: {test_file.stem}")
				return run_specific_test_file(f"integration/{test_file.name}", verbosity)

	print(f"No test found matching: {test_name}")
	return False


def main():
	"""Main entry point for the modular test runner."""
	parser = argparse.ArgumentParser(
		description="Modular test runner for ignition-lint",
		formatter_class=argparse.RawDescriptionHelpFormatter, epilog="""
	Examples:
		python test_runner.py --run-unit                    # Run all unit tests
		python test_runner.py --run-integration             # Run all integration tests
		python test_runner.py --run-config                  # Run configuration-driven tests
		python test_runner.py --run-all                     # Run all tests
		python test_runner.py --list                        # List available tests
		python test_runner.py --setup                       # Set up test environment
		python test_runner.py --run-config --tags component_naming
															# Run tests with specific tags
		python test_runner.py --test component_naming       # Run specific test by name
		python test_runner.py --unit-pattern "test_component*" # Run unit tests matching pattern
	"""
	)

	# Test execution options
	parser.add_argument("--run-unit", action="store_true", help="Run unit tests")
	parser.add_argument("--run-integration", action="store_true", help="Run integration tests")
	parser.add_argument("--run-config", action="store_true", help="Run configuration-driven tests")
	parser.add_argument("--run-all", action="store_true", help="Run all available tests")

	# Specific test execution
	parser.add_argument("--test", help="Run a specific test by name (supports partial matching)")
	parser.add_argument("--unit-pattern", help="Pattern for discovering unit tests (e.g., 'test_component*')")
	parser.add_argument("--integration-pattern", help="Pattern for discovering integration tests")

	# Configuration and setup options
	parser.add_argument("--create-configs", action="store_true", help="Create sample test configuration files")
	parser.add_argument("--setup", action="store_true", help="Set up the test environment")

	# Test filtering and information
	parser.add_argument("--tags", nargs="+", help="Filter configuration tests by tags")
	parser.add_argument("--list", action="store_true", help="List all available tests")

	# Output options
	parser.add_argument(
		"--verbose", "-v", action="count", default=1, help="Increase verbosity (use -vv for more verbose)"
	)
	parser.add_argument("--quiet", "-q", action="store_true", help="Reduce verbosity")

	args = parser.parse_args()

	# Set verbosity level
	if args.quiet:
		verbosity = 0
	else:
		verbosity = min(args.verbose, 2)

	# Handle setup first
	if args.setup:
		setup_test_environment()
		return 0

	# Handle list command
	if args.list:
		list_available_tests()
		return 0

	# Handle config creation
	if args.create_configs:
		create_sample_test_configs()
		return 0

	# Handle specific test execution
	if args.test:
		success = run_test_by_name(args.test, verbosity)
		return 0 if success else 1

	# Determine which tests to run
	run_unit = args.run_unit or args.run_all
	run_integration = args.run_integration or args.run_all
	run_config = args.run_config or args.run_all

	if not (run_unit or run_integration or run_config):
		print("No test type specified. Use --run-unit, --run-integration, --run-config, or --run-all")
		parser.print_help()
		return 1

	success = True

	# Run unit tests
	if run_unit:
		print("=" * 60)
		print("RUNNING UNIT TESTS")
		print("=" * 60)
		success = discover_and_run_unit_tests(args.unit_pattern, verbosity) and success

	# Run integration tests
	if run_integration:
		print("\n" + "=" * 60)
		print("RUNNING INTEGRATION TESTS")
		print("=" * 60)
		success = discover_and_run_integration_tests(args.integration_pattern, verbosity) and success

	# Run configuration tests
	if run_config:
		print("\n" + "=" * 60)
		print("RUNNING CONFIGURATION-DRIVEN TESTS")
		print("=" * 60)
		success = run_config_tests(tags=args.tags) and success

	# Final result
	print("\n" + "=" * 60)
	if success:
		print("ALL TESTS PASSED ✅")
		return 0
	else:
		print("SOME TESTS FAILED ❌")
		return 1


if __name__ == "__main__":
	sys.exit(main())
