""" This script is used to lint Ignition view.json files for style inconsistencies in component and parameter names. """

import json
import sys
import argparse
import os
import glob
import re
from .checker import StyleChecker


class JsonLinter:
	"""Class for linting Ignition view.json files for style inconsistencies in component and parameter names."""

	def __init__(self, component_style, parameter_style, component_style_rgx, parameter_style_rgx, allow_acronyms=False):
		# Check if both named style and regex style are provided for the same type
		if component_style_rgx not in [None, ""] and component_style not in [None, ""]:
			message = "Cannot specify both (component_style: {}, component_style_rgx: {}). Please choose one or the other."
			raise ValueError(message.format(component_style, component_style_rgx))

		if parameter_style_rgx not in [None, ""] and parameter_style not in [None, ""]:
			message = "Cannot specify both (parameter_style: {}, parameter_style_rgx: {}). Please choose one or the other."
			raise ValueError(message.format(parameter_style, parameter_style_rgx))

		if component_style_rgx is None and component_style is None:
			raise ValueError("Component naming style not specified. Use either (component_style) or (component_style_rgx).")

		if parameter_style_rgx is None and parameter_style is None:
			raise ValueError("Parameter naming style not specified. Use either (parameter_style) or (parameter_style_rgx).")

		if parameter_style == "Title Case":
			raise ValueError("Title Case is not a valid parameter naming style. Please use a different style.")

		self.parameter_areas = ["custom", "params"]
		self.component_areas = ["root", "children"]
		self.keys_to_skip = [
			"props",
			"position",
			"type",
			"meta",
			"propConfig",
			"scripts",
		]
		self.component_style = component_style
		self.parameter_style = parameter_style
		self.component_style_rgx = component_style_rgx
		self.parameter_style_rgx = parameter_style_rgx
		self.allow_acronyms = allow_acronyms
		self.errors = {"components": [], "parameters": []}
		self.files_linted = 0

		self.component_style_checker = StyleChecker(component_style_rgx if component_style_rgx else component_style, allow_acronyms)
		self.parameter_style_checker = StyleChecker(parameter_style_rgx if parameter_style_rgx else parameter_style, allow_acronyms)

	def _should_skip_key(self, key: str) -> bool:
		"""Determine if a key should be skipped."""
		return key in self.keys_to_skip or key.startswith("$")

	def _build_key_path(self, parent_key: str, key: str) -> str:
		"""Build the full key path from parent_key and key."""
		return f"{parent_key}.{key}" if parent_key else key

	def _clean_key(self, key: str) -> str:
		"""Clean the key by removing any parent path before the last dot."""
		return key.rsplit('.', 1)[-1] if '.' in key else key

	def _add_error_if_valid(self, errors: dict, key_path: str, parent_key: str) -> None:
		"""Add an error to the errors dict if it meets the conditions."""
		if "props.params" not in parent_key and key_path not in errors["parameters"]:
			errors["parameters"].append(key_path)

	def lint_file(self, file_path: str) -> int:
		"""Lint the file at the given path.

		Args:
		file_path (str): The path to the file to be linted.

		Returns: 
		int: The number of errors found in the file.
		"""
		if re.search(r"[\*\?\[\]]", file_path):
			files = glob.glob(file_path, recursive=True)
			if not files:
				print(f"No files found matching the pattern: {file_path}")
				return 0

			num_errors = 0
			for file in files:
				num_errors += self.lint_single_file(file)
			return num_errors
		return self.lint_single_file(file_path)

	def lint_single_file(self, file_path: str) -> int:
		"""Lint a single file.

		Args:
		file_path (str): The path to the file to be linted.

		Returns:
		int: The number of errors found in the file.
		"""
		if not os.path.exists(file_path):
			print(f"File not found: {file_path}")
			return 0

		if os.path.basename(file_path) != "view.json":
			return 0

		self.errors = {"components": [], "parameters": []}

		with open(file_path, "r", encoding="utf-8") as file:
			try:
				data = json.load(file)
				# Check root-level propConfig explicitly because non-persitent properties are not included in custom or params
				if "propConfig" in data:
					self.check_parameter_names(data["propConfig"], self.errors, "view", recursive=False)
				# Then proceed with recursive component checks
				self.check_component_names(data, self.errors)
			except json.JSONDecodeError as e:
				print(f"Error parsing file {file_path}: {e}")
				return 0

		self.print_errors(file_path, self.errors)
		num_errors = len(self.errors["components"]) + len(self.errors["parameters"])

		self.files_linted += 1
		return num_errors

	def check_parameter_names(self, data, errors: dict, parent_key: str = "", recursive: bool = True):
		"""Check the parameter names in the data."""
		for key, value in data.items():
			# Skip keys that should be ignored
			if self._should_skip_key(key):
				continue

			# Build the full key path and clean the key for style checking
			key_path = self._build_key_path(parent_key, key)
			clean_key = self._clean_key(key)

			# Check style and add to errors if necessary
			if not self.parameter_style_checker.is_correct_style(clean_key):
				self._add_error_if_valid(errors, key_path, parent_key)

			# Recurse into nested dictionaries if enabled
			if recursive and isinstance(value, dict):
				self.check_parameter_names(value, errors, key_path)

	def check_component_names(self, value, errors: dict, parent_key: str = ""):
		"""Check the component names in the data."""
		component_name = value.get("meta", {}).get("name")
		if component_name == "root":
			parent_key = component_name
		elif component_name is not None:
			parent_key = f"{parent_key}/{component_name}"
			if not self.component_style_checker.is_correct_style(component_name):
				errors["components"].append(parent_key)

		for key, element in value.items():
			if key in self.keys_to_skip:
				continue

			if isinstance(element, dict):
				if key in self.parameter_areas:
					if not parent_key:
						parent_key = "view"
					self.check_parameter_names(element, errors, f"{parent_key}.{key}")
				else:
					self.check_component_names(element, errors, parent_key)
			elif isinstance(element, list):
				parent_of_list = parent_key
				for item in element:
					self.check_component_names(item, errors, parent_key)
					parent_key = parent_of_list

	def print_errors(self, file_path: str, errors: dict) -> None:
		"""Print the errors found in the file."""
		error_logs = []
		if errors["components"]:
			if self.component_style_rgx:
				error_logs.append(f"  Component names should follow pattern '{self.component_style_rgx}':")
			else:
				error_logs.append(f"  Component names should be in {self.component_style}:")
			error_logs.extend([f"    - {error}" for error in errors["components"]])
		if errors["parameters"]:
			if self.parameter_style_rgx:
				error_logs.append(f"  Parameter names should follow pattern '{self.parameter_style_rgx}':")
			else:
				error_logs.append(f"  Parameter keys should be in {self.parameter_style}:")
			error_logs.extend([f"    - {error}" for error in errors["parameters"]])

		if error_logs:
			print(f"\nError in file: {file_path}")
			for error_log in error_logs:
				print(error_log)


def main():
	"""Main function to lint Ignition view.json files for style inconsistencies."""
	parser = argparse.ArgumentParser(description="Lint Ignition JSON files")
	parser.add_argument(
		"--files",
		help="Comma-separated list of files or glob patterns to lint",
	)
	parser.add_argument(
		"--component-style",
		default="PascalCase",
		help="Naming convention style for components",
	)
	parser.add_argument(
		"--parameter-style",
		default="camelCase",
		help="Naming convention style for parameters",
	)
	parser.add_argument(
		"--component-style-rgx",
		help="Regex pattern for naming convention style of components",
	)
	parser.add_argument(
		"--parameter-style-rgx",
		help="Regex pattern for naming convention style of parameters",
	)
	parser.add_argument(
		"--allow-acronyms",
		action="store_true",
		help="Allow acronyms in naming styles",
	)
	parser.add_argument("filenames", nargs="*", help="Filenames to check. These are passed by pre-commit.")
	args = parser.parse_args()

	linter = JsonLinter(
		component_style=args.component_style,
		parameter_style=args.parameter_style,
		component_style_rgx=args.component_style_rgx,
		parameter_style_rgx=args.parameter_style_rgx,
		allow_acronyms=args.allow_acronyms,
	)
	number_of_errors = 0

	if args.files:
		files_to_lint = args.files.split(",")
		for file_pattern in files_to_lint:
			matched_files = glob.glob(file_pattern, recursive=True)
			for file_path in matched_files:
				number_of_errors += linter.lint_file(file_path)
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
