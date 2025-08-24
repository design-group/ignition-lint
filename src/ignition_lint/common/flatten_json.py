"""
This module takes a JSON file and flattens it based on the defined features.
"""

import json
import logging
import sys
import re
from collections import OrderedDict
from pathlib import Path

UNICODE_REPLACEMENTS = {
	r"\\u003c": "UNICODE_LT",
	r"\\u003e": "UNICODE_GT",
	r"\\u0026": "UNICODE_AMP",
	r"\\u003d": "UNICODE_EQ",
	r"\\u0027": "UNICODE_APOS",
}
UNICODE_RESTORE = {v: k for k, v in UNICODE_REPLACEMENTS.items()}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)


def preserve_unicode_escapes(text):
	"""Preserve specific Unicode escapes in JSON content."""
	for escape, placeholder in UNICODE_REPLACEMENTS.items():
		text = re.sub(escape, placeholder, text)
	return text


def restore_unicode_escapes(text):
	"""Restore Unicode escapes from placeholders."""
	for placeholder, escape in UNICODE_RESTORE.items():
		# We need to use a raw string for the replacement to handle backslashes properly
		text = text.replace(placeholder, escape.replace('\\\\', '\\'))
	return text


def format_json(obj):
	"""Format JSON with 2-space indentation and no trailing whitespace.

	Args:
		obj: JSON-serializable object.

	Returns:
		str: Formatted JSON string.
	"""
	return json.dumps(obj, indent=2, ensure_ascii=False).rstrip()


def read_json_file(file_path):
	"""Read and parse a JSON file while preserving Unicode escapes.

	Args:
		file_path (Path): Path to the JSON file.

	Returns:
		OrderedDict: Parsed JSON data.

	Raises:
		SystemExit: If the file is not found or JSON is invalid.
	"""
	file_path = Path(file_path).resolve()
	try:
		with file_path.open("r", encoding="utf-8") as file:
			content = file.read()
			return json.loads(content, object_pairs_hook=OrderedDict)
			# preserved_content = preserve_unicode_escapes(content)
			# return json.loads(preserved_content, object_pairs_hook=OrderedDict)
	except FileNotFoundError:
		LOGGER.error("File %s not found. Confirm the file exists and is accessible.", file_path)
		sys.exit(1)
	except json.JSONDecodeError as e:
		LOGGER.error("Invalid JSON in %s: %s", file_path, e)
		sys.exit(1)


def write_json_file(file_path, data):
	"""Write formatted JSON to a file, restoring Unicode escapes.

	Args:
		file_path (Path): Path to the JSON file.
		data: JSON-serializable object.

	Raises:
		SystemExit: If the file cannot be written.
	"""
	file_path = Path(file_path).resolve()
	try:
		# Ensure the parent directory exists
		file_path.parent.mkdir(parents=True, exist_ok=True)

		formatted_json = format_json(data)
		# restored_content = restore_unicode_escapes(formatted_json)
		with file_path.open("w", encoding="utf-8", newline="\n") as file:
			# file.write(restored_content)
			file.write(formatted_json)
	except (OSError, IOError) as e:
		LOGGER.error("Failed to write %s: %s", file_path, e)
		sys.exit(1)


def _get_component_path(data, path):
	"""Extract component name and update path for better clarity."""
	component_name = data.get('meta', {}).get('name')
	if component_name:
		return f"{path}.{component_name}" if path else component_name
	return path


def _process_dict_item(key, value, path, results):
	"""Process a single key-value pair from a dictionary."""
	current_path = f"{path}.{key}" if path else key
	if isinstance(value, dict):
		flatten_json(value, current_path, results)
	elif isinstance(value, list):
		_process_list_items(value, current_path, results)
	else:
		results[current_path] = value


def _process_list_items(items, base_path, results):
	"""Process all items in a list."""
	for index, item in enumerate(items):
		item_path = f"{base_path}[{index}]"
		_process_single_item(item, item_path, results)


def _process_single_item(item, item_path, results):
	"""Process a single item, whether primitive or complex."""
	if isinstance(item, (dict, list)):
		flatten_json(item, item_path, results)
	else:
		results[item_path] = item


def flatten_json(data, path="", results=None):
	"""
	Recursively flattens a JSON-like dictionary into path-to-value pairs.

	Args:
		data (dict): The JSON data to flatten.
		path (str): The current path being traversed (used internally).
		results (dict): The dictionary to store the results (used internally).

	Returns:
		dict: A flattened dictionary where keys are paths and values are primitive values.
	"""
	if results is None:
		results = OrderedDict()

	if isinstance(data, dict):
		path = _get_component_path(data, path)
		for key, value in data.items():
			_process_dict_item(key, value, path, results)
	elif isinstance(data, list):
		base_path = path if path else ""
		for index, item in enumerate(data):
			item_path = f"{base_path}[{index}]" if base_path else f"[{index}]"
			_process_single_item(item, item_path, results)

	return results


def flatten_file(file_path):
	"""Flatten a JSON file and return sorted results.
	
	Args:
		file_path: Path to the JSON file.
		
	Returns:
		OrderedDict: Sorted flattened JSON data.
	"""
	json_data = read_json_file(file_path)
	flat_json = flatten_json(json_data)
	return OrderedDict(sorted(flat_json.items()))
