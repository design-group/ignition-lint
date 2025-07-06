"""
This module contains common and base node types for rule implementation
"""

from abc import ABC, abstractmethod
from typing import Set, List, Dict
from ..model.node_types import ViewNode, NodeType, ScriptNode


class NodeVisitor(ABC):
	"""Simplified base visitor class that rules can extend."""

	def visit_generic(self, node: ViewNode):
		"""Generic visit method for nodes that don't have specific handlers."""
		pass

	# Specific visit methods - rules only need to implement what they care about
	def visit_component(self, node: ViewNode):
		pass

	def visit_expression_binding(self, node: ViewNode):
		pass

	def visit_property_binding(self, node: ViewNode):
		pass

	def visit_tag_binding(self, node: ViewNode):
		pass

	def visit_message_handler(self, node: ViewNode):
		pass

	def visit_custom_method(self, node: ViewNode):
		pass

	def visit_transform(self, node: ViewNode):
		pass

	def visit_event_handler(self, node: ViewNode):
		pass

	def visit_property(self, node: ViewNode):
		pass


class LintingRule(NodeVisitor):
	"""Base class for linting rules with simplified interface."""

	def __init__(self, target_node_types: Set[NodeType] = None):
		"""
        Initialize the rule.
        
        Args:
            target_node_types: Set of node types this rule applies to. 
                              If None, applies to all nodes.
        """
		self.target_node_types = target_node_types or set()
		self.errors = []

	def applies_to(self, node: ViewNode) -> bool:
		"""Check if this rule applies to the given node."""
		return node.applies_to_rule(self.target_node_types)

	def process_nodes(self, nodes: List[ViewNode]):
		"""Process a list of nodes, applying the rule to applicable ones."""
		self.errors = []  # Reset errors

		# Filter nodes that this rule applies to
		applicable_nodes = [node for node in nodes if self.applies_to(node)]

		# Visit each applicable node
		for node in applicable_nodes:
			node.accept(self)

		# Allow for batch processing if needed
		self.post_process()

	def post_process(self):
		"""Override this method if you need to do batch processing after visiting all nodes."""
		pass

	@property
	@abstractmethod
	def error_message(self) -> str:
		"""Return a description of what this rule checks for."""
		pass

	@property
	def error_key(self) -> str:
		"""Key to use in the errors dict for this rule."""
		return self.__class__.__name__


class BindingRule(LintingRule):
	"""Base class for binding-specific rules."""

	def __init__(self, target_node_types: Set[NodeType] = None):
		if target_node_types is None:
			target_node_types = NodeType.ALL_BINDINGS()
		super().__init__(target_node_types)


class ScriptRule(LintingRule):
	"""Base class for script-specific rules with built-in script collection."""

	def __init__(self, target_node_types: Set[NodeType] = None):
		if target_node_types is None:
			target_node_types = NodeType.ALL_SCRIPTS()
		super().__init__(target_node_types)
		self.collected_scripts = {}

	def visit_message_handler(self, node: ViewNode):
		self._collect_script(node)

	def visit_custom_method(self, node: ViewNode):
		self._collect_script(node)

	def visit_transform(self, node: ViewNode):
		self._collect_script(node)

	def visit_event_handler(self, node: ViewNode):
		self._collect_script(node)

	def _collect_script(self, node: ViewNode):
		"""Collect script for batch processing."""
		if isinstance(node, ScriptNode):
			self.collected_scripts[node.path] = node

	def post_process(self):
		"""Process all collected scripts in batch."""
		if self.collected_scripts:
			self.process_scripts(self.collected_scripts)
			self.collected_scripts = {}

	@abstractmethod
	def process_scripts(self, scripts: Dict[str, ScriptNode]):
		"""Process the collected scripts. Override in subclasses."""
		pass
