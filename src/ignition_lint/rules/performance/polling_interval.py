"""
Polling interval validation rule for tag bindings.

This rule checks that tag bindings have appropriate polling intervals
to prevent performance issues in Ignition Perspective views.
"""

import re
from ..common import BindingRule
from ...model.node_types import ALL_BINDINGS


class PollingIntervalRule(BindingRule):
	"""Rule to check polling intervals in expressions."""

	def __init__(self, minimum_interval=10000, severity="error"):
		super().__init__(ALL_BINDINGS, severity)
		self.minimum_interval = minimum_interval

	@property
	def error_message(self) -> str:
		return f"Polling interval below minimum of {self.minimum_interval}ms"

	def visit_expression_binding(self, node):
		"""Check expression bindings for polling issues."""
		if 'now' in node.expression:
			if not self._is_valid_polling(node.expression):
				# Performance issues - use configured severity
				self.add_violation(f"{node.path}: '{node.expression}'")

	def visit_expression_struct_binding(self, node):
		"""Check expression struct bindings for polling issues in each expression."""
		for key, expression in node.struct.items():
			if 'now' in expression:
				if not self._is_valid_polling(expression):
					# Performance issues - use configured severity
					self.add_violation(f"{node.path}.{key}: '{expression}'")

	def visit_query_binding(self, node):
		"""Check query bindings for polling issues in parameter expressions."""
		for param_name, expression in node.parameters.items():
			if 'now' in expression:
				if not self._is_valid_polling(expression):
					# Performance issues - use configured severity
					self.add_violation(f"{node.path}.{param_name}: '{expression}'")

	def visit_tag_binding(self, node):
		"""Check tag bindings for polling issues in expressions based on mode."""
		if node.mode == 'expression':
			# Expression mode: tagPath is an expression
			if 'now' in node.tag_path:
				if not self._is_valid_polling(node.tag_path):
					# Performance issues - use configured severity
					self.add_violation(f"{node.path}: '{node.tag_path}'")

		elif node.mode == 'indirect':
			# Indirect mode: check reference expressions
			for ref_key, expression in node.references.items():
				if 'now' in expression:
					if not self._is_valid_polling(expression):
						# Performance issues - use configured severity
						self.add_violation(f"{node.path}.references.{ref_key}: '{expression}'")

		# Direct mode has no expressions to check

	def _is_valid_polling(self, expression):
		"""Check if the polling interval in an expression is valid."""
		if 'now' not in expression:
			return True

		pattern = r'now\s*\(\s*(\d*)\s*\)'
		matches = re.findall(pattern, expression)

		if not matches:
			alt_pattern = r'now\s*\('
			return not bool(re.search(alt_pattern, expression))

		for interval_str in matches:
			if not interval_str.strip():
				return False
			try:
				interval = int(interval_str)
				if 0 < interval < self.minimum_interval:
					return False
			except ValueError:
				return False

		return True
