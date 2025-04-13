"""
This module adds a rule to check component naming style consistency.
"""

import re
from .common import LintingRule


class ExpressionPollingRule(LintingRule):
	"""Rule to check component naming style consistency."""

	def __init__(self, min_interval):
		self.min_interval = min_interval
		self.keys_to_skip = []

	@property
	def error_key(self) -> str:
		return "polling"

	@property
	def error_message(self) -> str:
		return f"Excessive polling rate, or below minimum threshold of {self.min_interval}ms"

	def _should_skip_key(self, key: str) -> bool:
		return key in self.keys_to_skip or key.startswith("$")

	def _build_key_path(self, parent_key: str, key: str) -> str:
		if key in ['children', 'propConfig']:
			return parent_key
		return f"{parent_key}.{key}" if parent_key else key

	def _clean_key(self, key: str) -> str:
		return key.rsplit('.', 1)[-1] if '.' in key else key

	def _add_error_if_valid(self, errors: dict, detail: str = '') -> None:
		if self.key_path not in errors[self.error_key]:
			error_msg = f'{self.key_path}: {detail}' if detail else self.key_path
			errors[self.error_key].append(error_msg)

	def _parse_binding(self, errors: dict, config: dict) -> None:
		for key, value in config.items():
			if isinstance(value, (str)):
				if not self._is_valid_polling(value):
					self._add_error_if_valid(errors, detail=value)

			if isinstance(value, dict):
				self._parse_binding(errors, value)
			elif isinstance(value, list):
				for element in value:
					self._parse_binding(errors, element)

	def _is_valid_polling(self, expression) -> bool:
		if 'now' not in expression:
			return True

		# Pattern to match now() or now(<number>)
		pattern = r'now\((\d*)\)'
		matches = re.findall(pattern, expression)

		if not matches:  # Found 'now' but no matches means plain now()
			return False

		# Check each interval found in now(<interval>)
		for interval_str in matches:
			if not interval_str:  # Empty string means now() with no interval
				return False
			try:
				# interval of 0 is valid, as it only evaluates one time
				interval = int(interval_str)
				if interval > 0 and interval < self.min_interval:
					return False
			except ValueError:
				# If interval isn't a valid integer, conservatively flag as invalid
				return False

		return True

	def check(self, data, errors: dict, parent_key: str = ""):
		errors.setdefault(self.error_key, [])

		for key, value in data.items():
			if self._should_skip_key(key) or not isinstance(value, (list, dict)):
				continue

			self.key_path = self._build_key_path(parent_key, key)

			if isinstance(value, list):
				for item in value:
					key_name = item.get('meta', {}).get('name')
					parent_path = f'{self.key_path}.{key_name}' if key_name else self.key_path
					self.check(item, errors, parent_path)
			else:
				if "binding" in value.keys():
					self._parse_binding(errors, value['binding'])
					continue
				self.check(value, errors, self.key_path)
