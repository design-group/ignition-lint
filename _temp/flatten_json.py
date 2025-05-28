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
			preserved_content = preserve_unicode_escapes(content)
			return json.loads(preserved_content, object_pairs_hook=OrderedDict)
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
		restored_content = restore_unicode_escapes(formatted_json)
		with file_path.open("w", encoding="utf-8", newline="\n") as file:
			file.write(restored_content)
	except (OSError, IOError) as e:
		LOGGER.error("Failed to write %s: %s", file_path, e)
		sys.exit(1)


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

	# Handle component names for better path clarity
	component_name = data.get('meta', {}).get('name')
	if component_name:
		path = f"{path}.{component_name}" if path else component_name

	# Process each key-value pair
	if isinstance(data, dict):
		for key, value in data.items():
			current_path = f"{path}.{key}" if path else key

			if isinstance(value, dict):
				flatten_json(value, current_path, results)
			elif isinstance(value, list):
				# Process each item in the list, regardless of type
				for index, item in enumerate(value):
					item_path = f"{current_path}[{index}]"

					if isinstance(item, (dict, list)):
						# Recursively flatten complex items
						flatten_json(item, item_path, results)
					else:
						# Store primitive values directly
						results[item_path] = item
			else:
				# Store primitive values directly
				results[current_path] = value

	# Handle lists directly (for when a list is passed to the function)
	elif isinstance(data, list):
		for index, item in enumerate(data):
			item_path = f"{path}[{index}]" if path else f"[{index}]"

			if isinstance(item, (dict, list)):
				flatten_json(item, item_path, results)
			else:
				results[item_path] = item

	return results


if __name__ == "__main__":

	file_path = "tests/cases/ExpressionBindings/view.json"
	json_data = read_json_file(file_path)
	flat_json = flatten_json(json_data)
	sorted_data = OrderedDict(sorted(flat_json.items()))
	write_json_file("flat.json", sorted_data)
