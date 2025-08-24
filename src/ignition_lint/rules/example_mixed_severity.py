"""
Example rule demonstrating mixed severity within a single rule.
This shows how developers can append to both self.errors and self.warnings
based on the severity of different conditions.

SEVERITY GUIDELINES:
- Warnings: Style issues, recommendations, non-breaking problems
- Errors: Functional issues, breaking problems, security concerns

This is an EXAMPLE ONLY - not included in default rule configurations.
"""

from .common import LintingRule
from .registry import register_rule
from ..model.node_types import NodeType


@register_rule
class ExampleMixedSeverityRule(LintingRule):
	"""Example rule that can generate both warnings and errors for different conditions."""

	def __init__(self):
		super().__init__({NodeType.COMPONENT})

	@property
	def error_message(self) -> str:
		return "Component validation with mixed severity levels"

	def visit_component(self, component):
		"""
		Check components for different types of issues demonstrating severity levels.
		
		WARNING examples (style/recommendation issues):
		- Temporary naming patterns
		- Short names that hurt readability
		- Missing descriptive suffixes
		
		ERROR examples (functional/breaking issues):
		- Names indicating unsafe/test code in production
		- Conflicting naming patterns
		- Names that could cause runtime issues
		"""
		# WARNING: Style issue - temporary naming pattern
		if component.name.lower().startswith(('temp', 'test', 'tmp')):
			self.warnings.append(
				f"{component.path}: Component name '{component.name}' "
				f"uses temporary naming pattern (consider renaming for production)"
			)

		# ERROR: Functional issue - potentially unsafe component
		if component.name.lower() in ['unsafecomponent', 'debugcomponent', 'adminpanel']:
			self.errors.append(
				f"{component.path}: Component name '{component.name}' "
				f"indicates potentially unsafe or debug functionality"
			)

		# WARNING: Style issue - very short names hurt readability  
		if len(component.name) < 3 and not component.name.lower() in ['ok', 'no', 'go', 'id']:
			self.warnings.append(
				f"{component.path}: Component name '{component.name}' "
				f"is very short (consider more descriptive naming)"
			)

		# ERROR: Functional issue - conflicting indicators
		conflicting_patterns = [
			('debug', 'prod'), ('test', 'live'), ('dev', 'production'),
			('mock', 'real'), ('sample', 'actual')
		]
		name_lower = component.name.lower()
		for pattern1, pattern2 in conflicting_patterns:
			if pattern1 in name_lower and pattern2 in name_lower:
				self.errors.append(
					f"{component.path}: Component name '{component.name}' "
					f"contains conflicting indicators '{pattern1}' and '{pattern2}'"
				)
				break

		# WARNING: Style recommendation - missing component type suffix
		common_types = ['button', 'label', 'input', 'panel', 'container', 'table', 'chart']
		if (len(component.name) > 5 and 
			not any(comp_type in component.name.lower() for comp_type in common_types) and
			not component.name.lower().endswith(('btn', 'lbl', 'txt', 'img', 'icon'))):
			self.warnings.append(
				f"{component.path}: Component name '{component.name}' "
				f"might benefit from a descriptive suffix (e.g., Button, Label, Panel)"
			)