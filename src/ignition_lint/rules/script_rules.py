import tempfile
import os
import re
import shutil

from pylint import lint
from pylint.reporters.text import TextReporter
from io import StringIO

from .base import LintingRule
from ..model.node_types import (
	Binding,
	ExpressionBinding,
	PropertyBinding,
	TagBinding,
	Script,
	CustomMethodScript,
	MessageHandler,
	TransformScript,
	EventHandlerScript,
)


class ScriptLintingRule(LintingRule):
	"""Base class for rules that lint scripts."""

	def __init__(self, script_types=None):
		"""
        Initialize a script linting rule.
        
        Args:
            script_types: Specific script types to check (e.g., "messageHandler", "customMethod")
        """
		# Map script type names to node classes for registration
		type_to_class = {
			"script": Script,
			"messageHandler": MessageHandler,
			"customMethod": CustomMethodScript,
			"transformScript": TransformScript,
			"eventHandlerScript": EventHandlerScript
		}

		# Register Script base class and any specific script type classes
		node_types = [Script]
		if script_types:
			for script_type in script_types:
				if script_type in type_to_class:
					node_types.append(type_to_class[script_type])

		super().__init__(node_types=node_types, subtypes=script_types)
		self.scripts_to_check = {}

	# Collect scripts for batch processing
	def visit_script(self, script):
		"""Collect a script for later batch processing if it's a type we care about."""
		if self.applies_to(script):
			self.scripts_to_check[script.path] = script

	def process_collected_scripts(self):
		"""Process all collected scripts at once."""
		if not self.scripts_to_check:
			return

		# Convert dictionary to list of (path, script) tuples
		scripts_list = [(path, script) for path, script in self.scripts_to_check.items()]

		# Run pylint on all scripts at once
		path_to_issues = self._run_pylint_batch(scripts_list)

		# Add issues to our errors list
		for path, issues in path_to_issues.items():
			for issue in issues:
				self.errors.append(f"{path}: {issue}")

		# Clear the collected scripts
		self.scripts_to_check = {}


class PylintScriptRule(ScriptLintingRule):
	"""Rule to run pylint on scripts."""

	def __init__(self):
		super().__init__(script_types=["script", "messageHandler", "customMethod", "transformScript", "eventHandlerScript"])
		self.scripts_to_check = {}
		self.debug = False  # Set to True for debugging

	def visit_message_handler(self, handler):
		"""Collect a message handler for later batch processing."""
		self.scripts_to_check[handler.path] = handler

	def visit_custom_method(self, method):
		"""Collect a custom method for later batch processing."""
		self.scripts_to_check[method.path] = method

	def visit_script(self, script):
		"""Collect a script for later batch processing if it's a type we care about."""
		if self.applies_to(script):
			self.scripts_to_check[script.path] = script

	def visit_script_event_handler(self, handler):
		"""Collect a script event handler for later batch processing."""
		self.scripts_to_check[handler.path] = handler

	def process_collected_scripts(self):
		"""Process all collected scripts at once."""
		if not self.scripts_to_check:
			return

		# Convert dictionary to list of (path, script) tuples
		scripts_list = [(path, script) for path, script in self.scripts_to_check.items()]

		# Run pylint on all scripts at once
		path_to_issues = self._run_pylint_batch(scripts_list)

		# Add issues to our errors list
		for path, issues in path_to_issues.items():
			for issue in issues:
				self.errors.append(f"{path}: {issue}")

		# Clear the collected scripts
		self.scripts_to_check = {}

	def _run_pylint_batch(self, scripts):
		"""Run pylint on multiple scripts at once."""
		# Create a debug directory if it doesn't exist
		debug_dir = os.path.join(os.getcwd(), "debug")
		os.makedirs(debug_dir, exist_ok=True)

		# Map line numbers in the combined file back to script paths
		line_map = {}
		line_count = 1

		# Combine all scripts into one file with separator comments
		combined_code = []
		for i, script_item in enumerate(scripts):
			path = script_item[0]
			script_obj = script_item[1]

			# Add separator comment with script path
			header = f"# Script {i+1}: {path}"
			combined_code.append(header)
			line_count += 1

			# Get the script code, handling both string and object cases
			if hasattr(script_obj, 'get_formatted_code'):
				formatted_code = script_obj.get_formatted_code()
			elif hasattr(script_obj, 'code'):
				# It's a script object but doesn't have get_formatted_code
				formatted_code = f"def generic_script(self):\n    {script_obj.code.replace('\n', '\n    ')}"
			else:
				# It's probably a string
				code_str = script_obj if isinstance(script_obj, str) else str(script_obj)
				formatted_code = f"def generic_script(self):\n    {code_str.replace('\n', '\n    ')}"

			# Record line numbers for this script
			script_lines = formatted_code.count('\n') + 1
			for line_num in range(line_count, line_count + script_lines):
				line_map[line_num] = path

			# Add the formatted script code
			combined_code.append(formatted_code)
			line_count += script_lines

			# Add a blank line for separation
			combined_code.append("")
			line_count += 1

		# Join all code into a single string
		combined_code_str = "\n".join(combined_code)

		# Create a temporary file with all scripts
		with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
			temp_file_path = temp_file.name
			temp_file.write(combined_code_str.encode('utf-8'))

		# Also save a copy to the debug directory
		if self.debug:
			debug_file_path = os.path.join(debug_dir, os.path.basename(temp_file_path))
			shutil.copy2(temp_file_path, debug_file_path)

		# Prepare result container
		path_to_issues = {path: [] for path, _ in scripts}

		try:
			# Configure pylint with text reporter
			pylint_output = StringIO()
			reporter = TextReporter(pylint_output)

			# Set up pylint arguments
			args = [
				'--disable=all', '--enable=unused-import,undefined-variable,syntax-error', '--output-format=text',
				'--score=no', temp_file_path
			]

			# Run pylint
			lint.Run(args, reporter=reporter, exit=False)

			# Save the pylint output for debugging
			output = pylint_output.getvalue()
			with open(os.path.join(debug_dir, "pylint_output.txt"), 'w', encoding='utf-8') as f:
				f.write(output)

			# Parse text results
			if output:
				# Pattern to match pylint output lines
				pattern = r'.*:(\d+):\d+: .+: (.+)'
				for line in output.splitlines():
					match = re.match(pattern, line)
					if match:
						try:
							line_num = int(match.group(1))
							message = match.group(2)

							# Find which script this line belongs to
							script_path = None
							for ln in sorted(line_map.keys(), reverse=True):
								if ln <= line_num:
									script_path = line_map[ln]
									break

							if script_path and script_path in path_to_issues:
								# Calculate the line number relative to the start of the script
								script_start_line = min(
									ln for ln, path in line_map.items() if path == script_path
								)
								relative_line = line_num - script_start_line + 1
								path_to_issues[script_path].append(f"Line {relative_line}: {message}")
						except (ValueError, IndexError) as e:
							# Log the error for debugging
							with open(os.path.join(debug_dir, "pylint_error.txt"), 'a', encoding='utf-8') as f:
								f.write(f"Error parsing line: {line}\nException: {str(e)}\n\n")
							continue

		except Exception as e:
			# Handle exceptions and save error information
			error_msg = f"Error running pylint: {str(e)}"
			with open(os.path.join(debug_dir, "pylint_error.txt"), 'w', encoding='utf-8') as f:
				f.write(error_msg)

			for path in path_to_issues:
				path_to_issues[path].append(error_msg)

		finally:
			# Don't delete the temporary file if there were issues
			if any(issues for issues in path_to_issues.values()):
				# Copy it to the debug directory with a more helpful name
				shutil.copy(temp_file_path, os.path.join(debug_dir, "pylint_input_temp.py"))
				print(f"Pylint encountered issues. Debug files saved to: {debug_dir}")
			else:
				# Clean up the temporary file
				os.remove(temp_file_path)

		return path_to_issues
