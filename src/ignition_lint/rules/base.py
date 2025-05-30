# base.py
from abc import ABC, abstractmethod
from typing import Set, Union
from ..model.node_types import (
	ViewNode,
	Component,
	Binding,
	ExpressionBinding,
	PropertyBinding,
	TagBinding,
	Script,
	MessageHandlerScript,
	CustomMethodScript,
	TransformScript,
	EventHandler,
	EventHandlerScript,
	Property,
)
from ..model.node_types import NodeType


class Visitor(ABC):
	"""Base visitor interface for all node types."""

	def visit_component(self, component: Component):
		pass

	def visit_binding(self, binding: Binding):
		pass

	def visit_script(self, script: Script):
		pass

	def visit_event_handler(self, handler: EventHandler):
		pass

	def visit_property(self, prop: Property):
		pass

	def visit_expression_binding(self, binding: ExpressionBinding):
		self.visit_binding(binding)

	def visit_property_binding(self, binding: PropertyBinding):
		self.visit_binding(binding)

	def visit_tag_binding(self, binding: TagBinding):
		self.visit_binding(binding)

	def visit_message_handler(self, handler: MessageHandlerScript):
		self.visit_script(handler)

	def visit_custom_method(self, method: CustomMethodScript):
		self.visit_script(method)

	def visit_script_transform(self, transform: TransformScript):
		self.visit_script(transform)

	def visit_script_event_handler(self, handler: EventHandlerScript):
		self.visit_event_handler(handler)
		self.visit_script(handler)


class LintingRule(Visitor):
	"""Base class for all linting rules."""

	def __init__(self, applicable_types: Set[NodeType] = None):
		"""
		Initialize a linting rule.

		Args:
			applicable_types: Set of NodeType enum values this rule applies to.
		"""
		self.errors = []
		self._applicable_types = applicable_types or set()

	@property
	def error_key(self) -> str:
		"""Key to use in the errors dict for this rule."""
		return self.__class__.__name__

	@property
	def error_message(self) -> str:
		"""Message to display for errors of this rule."""
		return f"Error detected by {self.__class__.__name__}"

	def applies_to(self, node: 'ViewNode') -> bool:
		"""Check if this rule applies to the given node."""
		if not self._applicable_types:
			return True
		return any(node_type.applies_to(node) for node_type in self._applicable_types)
