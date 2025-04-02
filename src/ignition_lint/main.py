"""This script is used to lint Ignition view.json files for style inconsistencies in component and parameter names."""

import json
import sys
import argparse
import os
import glob
import re
from .rules import ComponentNameRule, ParameterNameRule


class JsonLinter:
	"""Class for linting Ignition view.json files for style inconsistencies in component and parameter names."""

	def __init__(self, rules: list):
		self.rules = rules
		self.errors = {}
		self.files_linted = 0

	def lint_file(self, file_path: str) -> int:
		if re.search(r"[\*\?\[\]]", file_path):
			files = glob.glob(file_path, recursive=True)
			if not files:
				print(f"No files found matching the pattern: {file_path}")
				return 0
			return sum(self.lint_single_file(file) for file in files)
		return self.lint_single_file(file_path)

	def lint_single_file(self, file_path: str) -> int:
		if not os.path.exists(file_path):
			print(f"File not found: {file_path}")
			return 0
		if os.path.basename(file_path) != "view.json":
			return 0

		self.errors = {}
		with open(file_path, "r", encoding="utf-8") as file:
			try:
				data = json.load(file)
				# Special handling for propConfig
				for rule in self.rules:
					# TODO: refactor this specific issue to handle propConfig only on the root level
					if isinstance(rule, ParameterNameRule) and "propConfig" in data:
						rule.check(data["propConfig"], self.errors, "view", recursive=False)
					rule.check(data, self.errors)
			except json.JSONDecodeError as e:
				print(f"Error parsing file {file_path}: {e}")
				return 0

		self.print_errors(file_path)
		self.files_linted += 1
		return sum(len(errors) for errors in self.errors.values())

	def print_errors(self, file_path: str) -> None:
		if not self.errors:
			return

		error_logs = []
		for rule in self.rules:
			error_list = self.errors.get(rule.error_key, [])
			if error_list:
				error_logs.append(f"  {rule.error_message}:")
				error_logs.extend([f"    - {error}" for error in error_list])

		if error_logs:
			print(f"\nError in file: {file_path}")
			for log in error_logs:
				print(log)


def main():
	"""Main function to lint Ignition view.json files for style inconsistencies."""
	parser = argparse.ArgumentParser(description="Lint Ignition JSON files")
	parser.add_argument("--files", default="**/view.json", help="Comma-separated list of files or glob patterns to lint")
	parser.add_argument("--component-style", default="PascalCase", help="Naming convention style for components")
	parser.add_argument("--parameter-style", default="camelCase", help="Naming convention style for parameters")
	parser.add_argument("--component-style-rgx", help="Regex pattern for component naming")
	parser.add_argument("--parameter-style-rgx", help="Regex pattern for parameter naming")
	parser.add_argument("--allow-acronyms", action="store_true", help="Allow acronyms in naming styles")
	parser.add_argument("filenames", nargs="*", help="Filenames to check (from pre-commit)")
	args = parser.parse_args()

	rules = [
		ComponentNameRule(args.component_style, args.component_style_rgx, args.allow_acronyms),
		ParameterNameRule(args.parameter_style, args.parameter_style_rgx, args.allow_acronyms, ["custom", "params"])
	]
	linter = JsonLinter(rules)
	number_of_errors = 0

	if args.files:
		for file_pattern in args.files.split(","):
			number_of_errors += linter.lint_file(file_pattern)
	elif args.filenames:
		for file_path in args.filenames:
			number_of_errors += linter.lint_file(file_path)
	else:
		print("No files specified or found")
		sys.exit(0)

	if not number_of_errors:
		print("No style inconsistencies found")
		sys.exit(0)
	sys.exit(1)


if __name__ == "__main__":
	main()
