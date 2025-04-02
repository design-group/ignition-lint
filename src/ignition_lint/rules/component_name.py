"""
This module adds a rule to check component naming style consistency.
"""
from .common import LintingRule, StyleChecker


class ComponentNameRule(LintingRule):
	"""Rule to check component naming style consistency."""

	def __init__(self, style: str, style_rgx: str, allow_acronyms: bool):
		if style_rgx not in [None, ""] and style not in [None, ""]:
			raise ValueError(f"Cannot specify both (component_style: {style}, component_style_rgx: {style_rgx}). Choose one.")
		if style_rgx is None and style is None:
			raise ValueError("Component naming style not specified. Use either (component_style) or (component_style_rgx).")

		self._style = style_rgx or style
		self.style_checker = StyleChecker(self._style, allow_acronyms)

	@property
	def error_key(self) -> str:
		return "components"

	@property
	def error_message(self) -> str:
		return f"Component names should follow '{self._style}'"

	def check(self, data, errors: dict, parent_key: str = ""):
		if self.error_key not in errors:
			errors[self.error_key] = []

		component_name = data.get("meta", {}).get("name")
		if component_name == "root":
			parent_key = component_name
		elif component_name is not None:
			parent_key = f"{parent_key}/{component_name}"
			if not self.style_checker.is_correct_style(component_name):
				errors[self.error_key].append(parent_key)

		for key, value in data.items():
			if key in ["props", "position", "type", "meta", "propConfig", "scripts"]:
				continue
			if isinstance(value, dict):
				self.check(value, errors, parent_key)
			elif isinstance(value, list):
				parent_of_list = parent_key
				for item in value:
					self.check(item, errors, parent_key)
					parent_key = parent_of_list
