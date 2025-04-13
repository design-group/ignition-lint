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
		LOGGER.error(f"File not found: {file_path}")
		sys.exit(1)
	except json.JSONDecodeError as e:
		LOGGER.error(f"Invalid JSON in {file_path}: {e}")
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
		LOGGER.error(f"Failed to write {file_path}: {e}")
		sys.exit(1)


def flatten_json(data, path="", results=None):
	"""
    Recursively searches a JSON-like dictionary for keys named "expression" and 
    returns a dictionary of paths to expression values.

    Args:
        data (dict): The JSON data to search.
        path (str): The current path being traversed (used internally).
        results (dict): The dictionary to store the results (used internally).

    Returns:
        dict: A dictionary where keys are paths to "expression" keys and values 
              are the corresponding expression values.  Returns an empty dict if no expressions found.
    """
	if results is None:
		results = OrderedDict()

	component_name = data.get('meta', {}).get('name')
	if component_name:
		path = f"{path}.{component_name}"

	for key, value in data.items():
		current_path = f"{path}.{key}" if path else key

		if isinstance(value, dict):
			flatten_json(value, current_path, results)
		elif isinstance(value, list):
			for index, item in enumerate(value):
				if isinstance(item, dict):
					flatten_json(item, f"{current_path}[{index}]", results)
		else:
			results[current_path] = value
	return results


def flatten_file(file_path):

	json_data = read_json_file(file_path)
	flat_json = flatten_json(json_data)
	return OrderedDict(sorted(flat_json.items()))
