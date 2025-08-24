"""
Example rule demonstrating mixed severity within a single rule.
This shows how developers can append to both self.errors and self.warnings.
"""

from .common import LintingRule
from ..model.node_types import NodeType


class ExampleMixedSeverityRule(LintingRule):
	"""Example rule that can generate both warnings and errors for different conditions."""

	def __init__(self):
		super().__init__({NodeType.COMPONENT})

	@property
	def error_message(self) -> str:
		return "Component validation with mixed severity levels"

	def visit_component(self, component):
		"""Check components for different types of issues."""
		# Style issue -> warning
		if component.name.startswith('temp'):
			self.warnings.append(
				f"{component.path}: Component name '{component.name}' "
				f"uses temporary naming (consider renaming)"
			)

		# Functional issue -> error
		if component.name == 'UnsafeComponent':
			self.errors.append(
				f"{component.path}: Component name '{component.name}' "
				f"indicates unsafe implementation"
			)

		# Another style issue -> warning
		if len(component.name) < 3:
			self.warnings.append(
				f"{component.path}: Component name '{component.name}' "
				f"is too short (minimum 3 characters recommended)"
			)

		# Another functional issue -> error
		if 'Debug' in component.name and component.name.endswith('Prod'):
			self.errors.append(
				f"{component.path}: Component name '{component.name}' "
				f"contains conflicting debug/prod indicators"
			)