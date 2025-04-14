from typing import Dict, List, Any
from .model.builder import ViewModelBuilder
from .rules.base import LintingRule


class ViewLinter:
	"""Lints Ignition views using the object model."""

	def __init__(self, rules=None):
		self.rules = rules or []
		self.model_builder = ViewModelBuilder()

	def register_rule(self, rule):
		"""Register a rule with the linter."""
		self.rules.append(rule)

	def lint(self, flattened_json: Dict[str, Any]) -> Dict[str, List[str]]:
		"""Lint the given flattened JSON and return errors."""
		# Build the object model
		model = self.model_builder.build_model(flattened_json)

		# Collect all nodes in a flat list
		all_nodes = []
		for node_list in model.values():
			all_nodes.extend(node_list)

		errors = {}

		# Apply each rule to applicable nodes
		for rule in self.rules:
			rule.errors = []  # Reset errors

			for node in all_nodes:
				if rule.applies_to(node):
					node.accept(rule)

			# Process any collected scripts in batch
			if hasattr(rule, 'process_collected_scripts'):
				rule.process_collected_scripts()

			if rule.errors:
				errors[rule.error_key] = rule.errors

		return errors
