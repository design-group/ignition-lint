import tempfile
import os
import re
import shutil
from io import StringIO
from pylint import lint
from pylint.reporters.text import TextReporter

from .base import LintingRule
from ..model.node_types import NodeType, ViewNode


class ScriptLintingRule(LintingRule):
	"""Base class for rules that lint scripts."""

	def __init__(self, node_types: set[NodeType] = None):
		"""
        Initialize a script linting rule.

        Args:
            node_types: Set of NodeType enum values to check (defaults to ALL_SCRIPTS).
        """
		if node_types is None:
			node_types = {NodeType.ALL_SCRIPTS}
		super().__init__(node_types)
		self.scripts_to_check = {}

	def visit_script(self, node: NodeType):
		"""Collect a script for later batch processing if it is a type we care about."""
		if self.applies_to(node):
			self.scripts_to_check[node.path] = node

	def process_collected_scripts(self):
		"""Process all collected scripts at once."""
		raise NotImplementedError("Subclasses must implement this method")


class PylintScriptRule(ScriptLintingRule):
	"""Rule to run pylint on scripts."""

	def __init__(self):
		super().__init__()
		self.debug = True  # Set to True for debugging

	def process_collected_scripts(self):
		"""Process all collected scripts at once."""
		if not self.scripts_to_check:
			return

		# Convert dictionary to list of (path, script) tuples
		scripts_list = [(path, script) for path, script in self.scripts_to_check.items()]
		print(f"Running pylint on {len(scripts_list)} scripts...")
		# Run pylint on all scripts at once
		path_to_issues = self._run_pylint_batch(scripts_list)

		# Add issues to our errors list
		if path_to_issues:  # Check if not None
			for path, issues in path_to_issues.items():
				for issue in issues:
					self.errors.append(f"{path}: {issue}")

		# Clear the collected scripts
		self.scripts_to_check = {}

	def _run_pylint_batch(self, scripts: list[tuple[str, ViewNode]]) -> dict[str, list[str]]:
		"""Run pylint on multiple scripts at once."""
		# Create a debug directory if it doesn't exist
		debug_dir = os.path.join(os.getcwd(), "debug")
		os.makedirs(debug_dir, exist_ok=True)

		# Map line numbers in the combined file back to script paths
		line_map = {}
		line_count = 1

		# Combine all scripts into one file with separator comments
		combined_scripts = [
			"# Stub for common globals",
			"system = None  # Simulated Ignition system object",
			"",
		]
		for i, (path, script_obj) in enumerate(scripts):
			# Add separator comment with script path
			header = f"# Script {i+1}: {path}"
			combined_scripts.append(header)
			line_count += 1

			# Get the script code
			if hasattr(script_obj, 'get_formatted_script'):
				formatted_script = script_obj.get_formatted_script()
			else:
				# Fallback for raw script or unexpected object
				code_str = script_obj.code if hasattr(script_obj, 'code') else str(script_obj)
				formatted_script = f"def generic_script(self):\n    {code_str.replace('\n', '\n    ')}"

			# Record line numbers for this script
			script_lines = formatted_script.count('\n') + 1
			for line_num in range(line_count, line_count + script_lines):
				line_map[line_num] = path

			# Add the formatted script code
			combined_scripts.append(formatted_script)
			line_count += script_lines

			# Add a blank line for separation
			combined_scripts.append("")
			line_count += 1

		# Join all scripts into a single string
		combined_scripts_str = "\n".join(combined_scripts)

		# Create a temporary file with all scripts
		temp_file_path = None
		path_to_issues = {path: [] for path, _ in scripts}
		try:
			with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
				temp_file_path = temp_file.name
				temp_file.write(combined_scripts_str.encode('utf-8'))

			# Save a copy to the debug directory
			if self.debug:
				debug_file_path = os.path.join(debug_dir, os.path.basename(temp_file_path))
				shutil.copy2(temp_file_path, debug_file_path)

			# Configure pylint with text reporter
			pylint_output = StringIO()
			args = [
				'--disable=all',
				'--enable=unused-import,undefined-variable,syntax-error',
				'--output-format=text',
				'--score=no',
				temp_file_path,
			]

			lint.Run(args, reporter=TextReporter(pylint_output), exit=False)

			# Save the pylint output for debugging if needed
			output = pylint_output.getvalue()
			if self.debug:
				with open(os.path.join(debug_dir, "pylint_output.txt"), 'w', encoding='utf-8') as f:
					f.write(output)

			# Parse text results
			pattern = r'.*:(\d+):\d+: .+: (.+)'
			for line in output.splitlines():
				match = re.match(pattern, line)
				if not match:
					continue
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
						script_start_line = min(
							ln for ln, path in line_map.items() if path == script_path
						)
						relative_line = line_num - script_start_line + 1
						path_to_issues[script_path].append(f"Line {relative_line}: {message}")
				except (ValueError, IndexError) as e:
					with open(
						os.path.join(debug_dir, "pylint_error.txt"), 'a', encoding='utf-8'
					) as f:
						f.write(f"Error parsing line: {line}\nException: {str(e)}\n\n")
					continue

		except Exception as e:
			error_msg = f"Error running pylint: {str(e)}"
			with open(os.path.join(debug_dir, "pylint_error.txt"), 'w', encoding='utf-8') as f:
				f.write(error_msg)
			for path in path_to_issues:
				path_to_issues[path].append(error_msg)

		finally:
			if temp_file_path and os.path.exists(temp_file_path):
				if any(issues for issues in path_to_issues.values()):
					shutil.copy(temp_file_path, os.path.join(debug_dir, "pylint_input_temp.py"))
					print(f"Pylint encountered issues. Debug files saved to: {debug_dir}")
				else:
					os.remove(temp_file_path)

		return path_to_issues
