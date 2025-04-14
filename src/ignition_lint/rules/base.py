from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any, Type
from ..model.node_types import (
	ViewNode,
	Component,
	Binding,
	ExpressionBinding,
	PropertyBinding,
	TagBinding,
	Script,
	MessageHandler,
	CustomMethodScript,
	Property,
	TransformScript,
	EventHandler,
	EventHandlerScript,
)


class Visitor(ABC):
	"""Base visitor interface for all node types."""

	# Base node types
	def visit_component(self, component: Component):
		"""Visit a component node."""
		pass

	def visit_binding(self, binding: Binding):
		"""Visit a generic binding node."""
		pass

	def visit_script(self, script: Script):
		"""Visit a generic script node."""
		pass

	def visit_event_handler(self, handler: EventHandler):
		"""Visit a generic event handler node."""
		pass

	def visit_property(self, prop: Property):
		"""Visit a property node."""
		pass

	# Specific binding types
	def visit_expression_binding(self, binding: ExpressionBinding):
		"""Visit an expression binding node."""
		self.visit_binding(binding)  # Default to generic binding behavior

	def visit_property_binding(self, binding: PropertyBinding):
		"""Visit a property binding node."""
		self.visit_binding(binding)  # Default to generic binding behavior

	def visit_tag_binding(self, binding: TagBinding):
		"""Visit a tag binding node."""
		self.visit_binding(binding)  # Default to generic binding behavior

	# Specific script types
	def visit_message_handler(self, handler: MessageHandler):
		"""Visit a message handler node."""
		self.visit_script(handler)  # Default to generic script behavior

	def visit_custom_method(self, method: CustomMethodScript):
		"""Visit a custom method node."""
		self.visit_script(method)  # Default to generic script behavior

	def visit_script_transform(self, transform: TransformScript):
		"""Visit a script transform node."""
		self.visit_script(transform)  # Default to generic script behavior

	# Event handler types
	def visit_script_event_handler(self, handler: EventHandlerScript):
		"""Visit a script event handler node."""
		self.visit_event_handler(handler)  # Treat as an event handler
		self.visit_script(handler)  # Also treat as a script


class LintingRule(Visitor):
	"""Base class for all linting rules."""

	def __init__(self, node_types=None, subtypes=None):
		"""
        Initialize a linting rule.
        
        Args:
            node_types: Base node types this rule applies to (e.g., Script, Binding)
            subtypes: Specific subtypes to check (e.g., "expression", "messageHandler")
        """
		self.errors = []
		self._applicable_node_types = set()
		self._node_subtypes = subtypes or []

		# Register node types
		if node_types:
			for node_type in node_types:
				self.register_node_type(node_type)

	@property
	def error_key(self) -> str:
		"""Key to use in the errors dict for this rule."""
		return self.__class__.__name__

	@property
	def error_message(self) -> str:
		"""Message to display for errors of this rule."""
		return f"Error detected by {self.__class__.__name__}"

	def applies_to(self, node) -> bool:
		"""Check if this rule applies to the given node."""
		node_type = type(node)

		# If no specific types registered, apply to all nodes
		if not self._applicable_node_types:
			return True

		# Check if the node's type is directly registered
		if node_type in self._applicable_node_types:
			# If no subtypes specified, accept all subtypes
			if not self._node_subtypes:
				return True

			# For script nodes, check the script_type attribute
			if isinstance(node, Script) and hasattr(node, 'script_type'):
				return node.script_type in self._node_subtypes

			# For binding nodes, check the binding_type or node class
			if isinstance(node, Binding):
				if isinstance(node, ExpressionBinding) and "expression" in self._node_subtypes:
					return True
				if isinstance(node, PropertyBinding) and "property" in self._node_subtypes:
					return True
				if isinstance(node, TagBinding) and "tag" in self._node_subtypes:
					return True

		return False

	def register_node_type(self, node_type):
		"""Register a node type this rule applies to."""
		self._applicable_node_types.add(node_type)
