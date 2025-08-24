"""
Shared test configuration and fixtures for ignition-lint tests.
This file contains common setup, fixtures, and utilities used across all tests.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ignition_lint.linter import LintEngine
from ignition_lint.rules import RULES_MAP
from ignition_lint.common.flatten_json import flatten_file


@pytest.fixture
def test_cases_dir():
	"""Fixture providing the path to test cases directory."""
	return Path(__file__).parent / "cases"


@pytest.fixture
def configs_dir():
	"""Fixture providing the path to test configs directory."""
	return Path(__file__).parent / "configs"


@pytest.fixture
def sample_view_files(test_cases_dir):
	"""Fixture providing paths to sample view files."""
	return {
		'pascal_case': test_cases_dir / "PascalCase" / "view.json",
		'camel_case': test_cases_dir / "camelCase" / "view.json",
		'snake_case': test_cases_dir / "snake_case" / "view.json",
		'kebab_case': test_cases_dir / "kebab-case" / "view.json",
		'inconsistent': test_cases_dir / "inconsistentCase" / "view.json",
		'expressions': test_cases_dir / "ExpressionBindings" / "view.json",
	}


@pytest.fixture
def lint_engine_factory():
	"""Factory fixture for creating lint engines with specific rules."""

	def _create_engine(rule_configs: Dict[str, Dict[str, Any]]):
		rules = []
		for rule_name, config in rule_configs.items():
			if rule_name in RULES_MAP:
				rule_class = RULES_MAP[rule_name]
				kwargs = config.get('kwargs', {})
				try:
					rules.append(rule_class(**kwargs))
				except Exception as e:
					pytest.fail(f"Failed to create rule {rule_name}: {e}")
		return LintEngine(rules)

	return _create_engine


@pytest.fixture
def run_lint():
	"""Fixture for running lint on a view file with given config."""

	def _run_lint(view_file: Path, rule_configs: Dict[str, Dict[str, Any]]):
		if not view_file.exists():
			pytest.skip(f"View file not found: {view_file}")

		# Create rules from config
		rules = []
		for rule_name, config in rule_configs.items():
			if rule_name in RULES_MAP:
				rule_class = RULES_MAP[rule_name]
				kwargs = config.get('kwargs', {})
				try:
					rules.append(rule_class(**kwargs))
				except Exception as e:
					pytest.fail(f"Failed to create rule {rule_name}: {e}")

		# Run linting
		lint_engine = LintEngine(rules)
		flattened_json = flatten_file(view_file)
		return lint_engine.process(flattened_json)

	return _run_lint
