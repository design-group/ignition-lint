"""This script is used to lint Ignition view.json files for style inconsistencies in component and parameter names."""

import json
import sys
import argparse
import os
import glob
from pathlib import Path

from .common.flatten_json import read_json_file, flatten_json
from .linter import ViewLinter
from .rules import RULES_MAP


def load_config(config_path: str) -> dict:
	"""Load configuration from a JSON file."""
	try:
		with open(config_path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except (FileNotFoundError, json.JSONDecodeError) as e:
		print(f"Error loading config file {config_path}: {e}")
		return {}


def create_rules_from_config(config: dict) -> list:
	"""Create rule instances from config dictionary."""
	rules = []
	for rule_name, rule_config in config.items():
		if not rule_config.get('enabled', True):
			continue

		if rule_name not in RULES_MAP:
			print(f"Unknown rule: {rule_name}")
			continue

		rule_class = RULES_MAP[rule_name]
		kwargs = rule_config.get('kwargs', {})
		rules.append(rule_class(**kwargs))

	return rules


def lint_file(file_path: str, rules: list) -> dict:
	"""Lint a single file with the given rules."""
	# Read and flatten the JSON file
	json_data = read_json_file(Path(file_path))
	flattened_json = flatten_json(json_data)

	# Create linter and lint the file
	linter = ViewLinter(rules)
	return linter.lint(flattened_json)


def print_file_errors(file_path: str, errors: dict) -> int:
	"""
    Print errors for a file and return the total number of errors.
    
    Args:
        file_path: Path to the file with errors
        errors: Dictionary mapping rule names to lists of error messages
    
    Returns:
        int: Total number of errors found
    """
	if not errors:
		return 0

	error_count = sum(len(error_list) for error_list in errors.values())

	if error_count > 0:
		print(f"\nFound {error_count} issues in {file_path}:")

		for rule_name, error_list in errors.items():
			if error_list:
				print(f"  {rule_name}:")
				for error in error_list:
					print(f"    - {error}")

	return error_count


def main():
	"""Main function to lint Ignition view.json files for style inconsistencies."""
	parser = argparse.ArgumentParser(description="Lint Ignition JSON files")
	parser.add_argument(
		"--config",
		default="rule_config.json",
		help="Path to configuration JSON file",
	)
	parser.add_argument(
		"--files",
		default="**/view.json",
		help="Comma-separated list of files or glob patterns to lint",
	)
	parser.add_argument(
		"filenames",
		nargs="*",
		help="Filenames to check (from pre-commit)",
	)
	args = parser.parse_args()

	# Load config and create rules
	config = load_config(args.config)
	if not config:
		sys.exit(1)

	rules = create_rules_from_config(config)

	if not rules:
		print("No valid rules configured")
		sys.exit(1)

	# Process files
	total_errors = 0
	files_linted = 0

	if args.filenames:
		for file_path in args.filenames:
			if os.path.exists(file_path):
				errors = lint_file(file_path, rules)
				# Print errors and update count
				file_errors = print_file_errors(file_path, errors)
				total_errors += file_errors
				files_linted += 1
	elif args.files:
		for file_pattern in args.files.split(","):
			for file_path in glob.glob(file_pattern.strip(), recursive=True):
				if os.path.exists(file_path) and os.path.basename(file_path) == "view.json":
					errors = lint_file(file_path, rules)
					# Print errors and update count
					file_errors = print_file_errors(file_path, errors)
					total_errors += file_errors
					files_linted += 1
	else:
		print("No files specified or found")
		sys.exit(0)

	if not total_errors:
		print(f"No style inconsistencies found in {files_linted} files")
		sys.exit(0)
	else:
		print(f"Found {total_errors} style inconsistencies in {files_linted} files")
		sys.exit(1)


if __name__ == "__main__":
	main()
