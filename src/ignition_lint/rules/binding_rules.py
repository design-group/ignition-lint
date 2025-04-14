import re
from .base import LintingRule
from ..model.node_types import Binding, ExpressionBinding, PropertyBinding, TagBinding


class BindingLintingRule(LintingRule):
	"""Base class for rules that lint bindings."""

	def __init__(self, binding_types=None):
		super().__init__()
		self.register_node_type(Binding)  # Register the base Binding type
		self.binding_types = binding_types or []  # List of binding types to check

		# Register specific binding types if provided
		if "expression" in self.binding_types:
			self.register_node_type(ExpressionBinding)
		if "property" in self.binding_types:
			self.register_node_type(PropertyBinding)
		if "tag" in self.binding_types:
			self.register_node_type(TagBinding)

	def applies_to(self, node):
		"""Check if this rule applies to the given node."""
		if isinstance(node, Binding):
			if not self.binding_types:  # If no specific types, apply to all bindings
				return True

			# Check if the node's binding type is in our list of types to check
			if isinstance(node, ExpressionBinding) and "expression" in self.binding_types:
				return True
			if isinstance(node, PropertyBinding) and "property" in self.binding_types:
				return True
			if isinstance(node, TagBinding) and "tag" in self.binding_types:
				return True

		return False  # Not a binding node or not a binding type we care about


class PollingIntervalRule(BindingLintingRule):
	"""Rule to check polling intervals in expressions."""

	def __init__(self, min_interval=10000):
		super().__init__(binding_types=["expression", "property"])
		self.min_interval = min_interval

	@property
	def error_message(self) -> str:
		return f"Polling interval below minimum of {self.min_interval}ms"

	def visit_expression_binding(self, binding):
		"""Check expression bindings for polling issues."""
		if 'now' in binding.expression:
			if not self._is_valid_polling(binding.expression):
				self.errors.append(f"{binding.path}: '{binding.expression}'")

	def _is_valid_polling(self, expression):
		"""
		Check if the polling interval in an expression is valid.
		
		Args:
			expression: The expression string to check
			
		Returns:
			bool: True if polling is valid or not present, False if invalid
		"""
		if 'now' not in expression:
			return True

		# Use a more flexible regex pattern that handles whitespace
		pattern = r'now\s*\(\s*(\d*)\s*\)'
		matches = re.findall(pattern, expression)

		if not matches:
			# Try an even more lenient pattern
			alt_pattern = r'now\s*\('
			if re.search(alt_pattern, expression):
				print("Found 'now(' but couldn't extract interval - assuming plain now()")
				return False
			else:
				print("'now' is in the string but doesn't match our patterns")
				# Dump the character codes to help debug
				print("Character codes:", [ord(c) for c in expression])
				return True

		for interval_str in matches:
			if not interval_str.strip():  # Empty string means now() with no interval
				return False
			try:
				interval = int(interval_str)
				print(f"Interval value: {interval}, min required: {self.min_interval}")
				if interval > 0 and interval < self.min_interval:
					print(f"Interval {interval} is below minimum {self.min_interval}")
					return False
			except ValueError as e:
				print(f"Error parsing interval: {e}")
				return False

		print("All intervals are valid")
		return True
