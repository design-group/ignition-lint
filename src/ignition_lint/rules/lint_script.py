import datetime
import tempfile
import os
import re
import shutil
from typing import Dict, List

from io import StringIO
from pylint import lint
from pylint.reporters.text import TextReporter

from .common import ScriptRule
from ..model.node_types import ScriptNode


class PylintScriptRule(ScriptRule):
	"""Rule to run pylint on all script types using the simplified interface."""

	def __init__(self):
		super().__init__()  # Targets all script types by default
		self.debug = True

	@property
	def error_message(self) -> str:
		return "Pylint detected issues in script"

	def process_scripts(self, scripts: Dict[str, ScriptNode]):
		"""Process all collected scripts with pylint."""
		if not scripts:
			return

		# Run pylint on all scripts at once
		path_to_issues = self._run_pylint_batch(scripts)

		# Add issues to our errors list
		for path, issues in path_to_issues.items():
			for issue in issues:
				self.errors.append(f"{path}: {issue}")

	def _run_pylint_batch(self, scripts: Dict[str, ScriptNode]) -> Dict[str, List[str]]:
		"""Run pylint on multiple scripts at once."""

		# Create a debug directory if it doesn't exist
		debug_dir = os.path.join(os.getcwd(), "debug")
		os.makedirs(debug_dir, exist_ok=True)

		# Map line numbers in the combined file back to script paths
		line_map = {}
		line_count = 1

		# Combine all scripts into one file with separator comments
		combined_scripts = [
			"#pylint: disable=unused-argument,missing-docstring,invalid-name,redefined-outer-name",
			"# Stub for common globals, and to simulate the Ignition environment",
			"system = None  # Simulated Ignition system object",
			"self = {} # Simulated self object for script context",
			"event = {}  # Simulated event object",
			"",
		]

		for i, (path, script_obj) in enumerate(scripts.items()):
			# Add separator comment with script path
			header = f"# Script {i+1}: {path}"
			combined_scripts.append(header)
			line_count += 1

			# Get the script code
			formatted_script = script_obj.get_formatted_script()

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
		path_to_issues = {path: [] for path in scripts.keys()}

		try:
			timestamp = datetime.datetime.now().strftime("%H%M%S")

			with tempfile.NamedTemporaryFile(
				prefix=f"{timestamp}_", suffix=".py", delete=False
			) as temp_file:
				temp_file_path = temp_file.name
				temp_file.write(combined_scripts_str.encode('utf-8'))

			# Save a copy to the debug directory
			if self.debug:
				_save_debug_file(temp_file_path, debug_dir)

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


def _save_debug_file(temp_file_path: str, debug_dir: str):
	"""Helper function to save temporary file to debug directory."""
	debug_file_path = os.path.join(debug_dir, os.path.basename(temp_file_path))
	shutil.copy2(temp_file_path, debug_file_path)

	# Keep only the 5 most recent debug files
	try:
		file_prefix = os.path.basename(temp_file_path).split('_')[0]
		# Get all .py files in the debug directory
		debug_files = [f for f in os.listdir(debug_dir) if f.endswith('.py') and os.path.basename(f).split('_')[0] != file_prefix]

		# Sort by modification time (newest first)
		debug_files.sort(key=lambda f: os.path.getmtime(os.path.join(debug_dir, f)), reverse=True)

		# Remove files beyond the 5 most recent
		for file_to_remove in debug_files[5:]:
			file_path = os.path.join(debug_dir, file_to_remove)
			os.remove(file_path)

	except OSError as e:
		# Handle potential file system errors gracefully
		print(f"Warning: Could not clean up old debug files: {e}")
