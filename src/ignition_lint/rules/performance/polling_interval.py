"""
Polling interval validation rule for tag bindings.

This rule checks that tag bindings have appropriate polling intervals
to prevent performance issues in Ignition Perspective views.
"""

import re
from ..common import BindingRule
from ...model.node_types import NodeType


class PollingIntervalRule(BindingRule):
	"""Rule to check polling intervals in expressions."""

	def __init__(self, minimum_interval=10000, severity="error"):
		super().__init__({NodeType.EXPRESSION_BINDING, NodeType.PROPERTY_BINDING, NodeType.TAG_BINDING}, severity)
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
