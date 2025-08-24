"""
This module implements a linting engine for processing ViewModel data from Ignition Perspective views.
It provides functionality to apply linting rules, collect errors, and analyze the structure of the view model.
It also includes methods for debugging nodes and analyzing rule impact on the view model.
"""

from typing import Dict, List, Any
from .rules.common import LintingRule
from .model.builder import ViewModelBuilder
from .model.node_types import NodeType, NodeUtils


class LintEngine:
	"""Simplified linter engine that processes nodes more efficiently."""

	def __init__(self, rules: List[LintingRule]):
		self.rules = rules
		self.model_builder = ViewModelBuilder()
		self.flattened_json = {}
		self.view_model = {}

	def _get_view_model(self) -> Dict[str, List[Any]]:
		"""Return the structured view model."""
		return self.model_builder.build_model(self.flattened_json)

	def process(self, flattened_json: Dict[str, Any]) -> Dict[str, List[str]]:
		"""Lint the given flattened JSON and return errors."""
		# Build the object model
		self.flattened_json = flattened_json
		self.view_model = self._get_view_model()

		# Collect all nodes in a flat list
		all_nodes = []
		for node_list in self.view_model.values():
			all_nodes.extend(node_list)

		errors = {}

		# Apply each rule to the nodes
		for rule in self.rules:
			# Let the rule process all nodes it's interested in
			rule.process_nodes(all_nodes)

			# Collect any errors from this rule
			if rule.errors:
				errors[rule.error_key] = rule.errors

		return errors

	def get_model_statistics(self, flattened_json: Dict[str, Any]) -> Dict[str, Any]:
		"""Get statistics about the parsed model for debugging/analysis."""
		self.flattened_json = flattened_json
		self.view_model = self._get_view_model()

		# Get all nodes for analysis
		all_nodes = []
		for node_list in self.view_model.values():
			all_nodes.extend(node_list)

		# Count by individual node types
		node_type_counts = {}
		for node_type in NodeType:
			count = len(NodeUtils.filter_by_types(all_nodes, {node_type}))
			if count > 0:  # Only include types that have nodes
				node_type_counts[node_type.value] = count

		# Count components by their actual type (Button, Label, etc.)
		components_by_type = {}
		component_nodes = NodeUtils.filter_by_types(all_nodes, {NodeType.COMPONENT})
		for comp in component_nodes:
			comp_type = getattr(comp, 'type', 'unknown')
			components_by_type[comp_type] = components_by_type.get(comp_type, 0) + 1

		# Get rule coverage statistics
		rule_coverage = self._get_rule_coverage_stats(all_nodes)

		stats = {
			'total_nodes': len(all_nodes),
			'node_type_counts': node_type_counts,
			'components_by_type': components_by_type,
			'rule_coverage': rule_coverage,
			'model_keys': list(self.view_model.keys()),
		}

		return stats

	def _get_rule_coverage_stats(self, all_nodes: List) -> Dict[str, Any]:
		"""Get statistics about which nodes each rule would process."""
		coverage = {}
		for rule in self.rules:
			rule_name = rule.__class__.__name__

			# Count how many nodes this rule would apply to
			if rule.target_node_types:
				applicable_nodes = NodeUtils.filter_by_types(all_nodes, rule.target_node_types)
				coverage[rule_name] = {
					'target_types': [nt.value for nt in rule.target_node_types],
					'applicable_node_count': len(applicable_nodes)
				}
			else:
				# Rule applies to all nodes
				coverage[rule_name] = {'target_types': ['all'], 'applicable_node_count': len(all_nodes)}

		return coverage

	def debug_nodes(self, flattened_json: Dict[str, Any], node_types: List[str] = None) -> List[Dict]:
		"""Get detailed information about nodes for debugging."""
		self.flattened_json = flattened_json
		self.view_model = self._get_view_model()

		all_nodes = []
		for node_list in self.view_model.values():
			all_nodes.extend(node_list)

		# Filter by node types if specified
		if node_types:
			target_types = set()

			for nt_str in node_types:
				try:
					target_types.add(NodeType(nt_str))
				except ValueError:
					print(
						f"Warning: Unknown node type '{nt_str}'. Available types: {[nt.value for nt in NodeType]}"
					)

			if target_types:
				all_nodes = NodeUtils.filter_by_types(all_nodes, target_types)

		# Return serialized node information
		return [node.serialize() for node in all_nodes]

	def analyze_rule_impact(self, flattened_json: Dict[str, Any]) -> Dict[str, Dict]:
		"""Analyze which nodes each rule would target."""
		self.flattened_json = flattened_json
		self.view_model = self._get_view_model()

		all_nodes = []
		for node_list in self.view_model.values():
			all_nodes.extend(node_list)

		analysis = {}
		for rule in self.rules:
			rule_name = rule.__class__.__name__

			if rule.target_node_types:
				applicable_nodes = NodeUtils.filter_by_types(all_nodes, rule.target_node_types)

				analysis[rule_name] = {
					'target_types': [nt.value for nt in rule.target_node_types],
					'applicable_nodes': len(applicable_nodes),
					'sample_paths': [node.path for node in applicable_nodes[:5]
							],  # First 5 as examples
					'node_details': [
						{
							'path': node.path,
							'type': node.node_type.value,
							'summary': self._get_node_summary(node)
						} for node in applicable_nodes[:3]  # First 3 with details
					]
				}
			else:
				analysis[rule_name] = {
					'target_types': ['all'],
					'applicable_nodes': len(all_nodes),
					'sample_paths': [node.path for node in all_nodes[:5]],
					'node_details': []  # Don't show details for rules that target everything
				}

		return analysis

	def _get_node_summary(self, node) -> str:
		"""Get a brief summary of what a node represents."""
		if node.node_type == NodeType.COMPONENT:
			return f"Component '{node.name}' of type '{getattr(node, 'type', 'unknown')}'"
		elif node.node_type == NodeType.EXPRESSION_BINDING:
			expr_preview = node.expression[:50] + '...' if len(node.expression) > 50 else node.expression
			return f"Expression: {expr_preview}"
		elif node.node_type == NodeType.TAG_BINDING:
			return f"Tag path: {getattr(node, 'tag_path', 'unknown')}"
		elif node.node_type == NodeType.PROPERTY_BINDING:
			return f"Property path: {getattr(node, 'target_path', 'unknown')}"
		elif hasattr(node, 'script'):
			script_preview = node.script[:30] + '...' if len(node.script) > 30 else node.script
			return f"Script: {script_preview}"
		else:
			return f"{node.node_type.value} node"
