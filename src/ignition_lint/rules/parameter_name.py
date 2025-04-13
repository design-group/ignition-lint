"""
This module adds a rule to check parameter naming style consistency.
"""
from .common import LintingRule, StyleChecker


class ParameterNameRule(LintingRule):
	"""Rule to check parameter naming style consistency."""

	def __init__(self, style_name: str, style_name_rgx: str, allow_acronyms: bool = False):
		if style_name_rgx not in [None, ""] and style_name not in [None, ""]:
			raise ValueError(f"Cannot specify both (style_name: {style_name}, style_name_rgx: {style_name_rgx}). Choose one.")
		if style_name_rgx is None and style_name is None:
			raise ValueError("Parameter naming style not specified. Use either (style_name) or (style_name_rgx).")
		if style_name == "Title Case":
			raise ValueError("Title Case is not a valid parameter naming style. Use a different style.")

		self._style = style_name_rgx or style_name
		self.style_checker = StyleChecker(self._style, allow_acronyms)
		self.keys_to_skip = ["props", "position", "type", "meta", "propConfig", "scripts"]

	@property
	def error_key(self) -> str:
		return "parameters"

	@property
	def error_message(self) -> str:
		return f"Parameter names should follow '{self._style}'"

	def _should_skip_key(self, key: str) -> bool:
		return key in self.keys_to_skip or key.startswith("$")

	def _build_key_path(self, parent_key: str, key: str) -> str:
		return f"{parent_key}.{key}" if parent_key else key

	def _clean_key(self, key: str) -> str:
		return key.rsplit('.', 1)[-1] if '.' in key else key

	def _add_error_if_valid(self, errors: dict, key_path: str, parent_key: str) -> None:
		if "props.params" not in parent_key and key_path not in errors[self.error_key]:
			errors[self.error_key].append(key_path)

	def check(self, data, errors: dict, parent_key: str = "", recursive: bool = True):
		errors.setdefault(self.error_key, [])

		for key, value in data.items():
			if self._should_skip_key(key):
				continue
			key_path = self._build_key_path(parent_key, key)
			clean_key = self._clean_key(key_path)

			if not self.style_checker.is_correct_style(clean_key):
				self._add_error_if_valid(errors, key_path, parent_key)

			if recursive and isinstance(value, dict):
				self.check(value, errors, key_path, recursive)
