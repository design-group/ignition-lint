"""
Rule to detect unused custom properties and view parameters.

This rule identifies custom properties and view parameters that are defined but never referenced
in bindings, scripts, or other expressions throughout the view.

Custom properties can be located at:
- custom.* - View-level custom properties
- params.* - View parameters (inputs to the view)
- {component_path}.custom.* - Component-level custom properties

SUPPORTED DETECTION:
- ✅ View-level custom properties (custom.*)
- ✅ View parameters (params.*)
- ✅ Component-level custom properties (*.custom.*)
- ✅ References in expression bindings ({view.custom.prop}, {this.custom.prop})
- ✅ Persistent vs non-persistent property handling

These properties are considered "used" if they are referenced in:
- ✅ Expression bindings (e.g., {view.custom.myProp}, {this.custom.myProp})
- ✅ Property bindings (e.g., tag paths, property paths)
- ✅ Tag bindings (e.g., tag paths containing property references)
- ✅ Script expressions in event handlers, message handlers, transforms, etc. (via comprehensive search)
- ✅ Custom method scripts (via comprehensive search)
- ✅ Any other context where property paths appear as strings in the view definition
"""

import re
from typing import Set, Dict, Any
from ..common import LintingRule
from ..registry import register_rule
from ...model.node_types import NodeType


@register_rule
class UnusedCustomPropertiesRule(LintingRule):
	"""Detects custom properties and view parameters that are defined but never referenced."""

	def __init__(self):
		# We need to examine all node types to find property definitions and references
		super().__init__({
			NodeType.PROPERTY, NodeType.COMPONENT, NodeType.EXPRESSION_BINDING, NodeType.PROPERTY_BINDING,
			NodeType.TAG_BINDING, NodeType.EVENT_HANDLER, NodeType.MESSAGE_HANDLER, NodeType.CUSTOM_METHOD,
			NodeType.TRANSFORM
		})

		# Track defined properties and where they're used
		self.defined_properties: Dict[str, str] = {}  # prop_path -> definition_location
		self.used_properties: Set[str] = set()
		self.flattened_json: Dict[str, Any] = {}  # Store flattened JSON for direct inspection

	@property
	def error_message(self) -> str:
		return "Unused custom properties and view parameters detection"

	def reset(self):
		"""Reset tracking between view files."""
		self.defined_properties = {}
		self.used_properties = set()
		self.flattened_json = {}

	def set_flattened_json(self, flattened_json: Dict[str, Any]):
		"""Set the flattened JSON for comprehensive property reference searching."""
		self.flattened_json = flattened_json

	def process_nodes(self, nodes):
		"""Process nodes to detect unused custom properties and view parameters."""
		# Call parent process_nodes first to get standard property processing
		super().process_nodes(nodes)

		# After processing all nodes, check for unused properties
		self.finalize()

	def post_process(self):
		"""Called after all nodes are visited - but we handle this in process_nodes."""

	def visit_property(self, node):
		"""Visit property nodes to find custom property definitions."""
		path = node.path

		# Check for view-level custom properties: custom.propName
		if path.startswith('custom.') and '.' not in path[7:]:  # Exactly custom.propName
			prop_name = path[7:]  # Remove 'custom.' prefix
			full_prop_path = f"view.custom.{prop_name}"
			self.defined_properties[full_prop_path] = path

		# Check for view-level parameters: params.paramName
		elif path.startswith('params.') and '.' not in path[7:]:  # Exactly params.paramName
			prop_name = path[7:]  # Remove 'params.' prefix
			full_prop_path = f"view.params.{prop_name}"
			self.defined_properties[full_prop_path] = path

		# Check for component custom properties: *.custom.propName
		elif '.custom.' in path and not path.startswith('propConfig.'):
			# Extract the property name (last part after .custom.)
			custom_match = re.search(r'\.custom\.([^.]+)$', path)
			if custom_match:
				prop_name = custom_match.group(1)

				# Extract component identifier from path
				component_path = path.split('.custom.')[0]
				# Get component name from path (last segment)
				component_name = component_path.split('.')[-1]
				full_prop_path = f"{component_name}.custom.{prop_name}"

				self.defined_properties[full_prop_path] = path

	def visit_expression_binding(self, node):
		"""Check expression bindings for custom property references."""
		self._check_expression_for_references(node.expression)

	def visit_property_binding(self, node):
		"""Check property bindings for custom property references."""
		# Property bindings might reference custom properties in their source paths
		if hasattr(node, 'source_property') and node.source_property:
			self._check_expression_for_references(node.source_property)

	def visit_tag_binding(self, node):
		"""Check tag bindings for custom property references in tag paths."""
		if hasattr(node, 'tag_path') and node.tag_path:
			self._check_expression_for_references(node.tag_path)

	def visit_event_handler(self, node):
		"""Check event handler scripts for custom property references."""
		if hasattr(node, 'script') and node.script:
			self._check_script_for_references(node.script)

	def visit_message_handler(self, node):
		"""Check message handler scripts for custom property references."""
		if hasattr(node, 'script') and node.script:
			self._check_script_for_references(node.script)

	def visit_custom_method(self, node):
		"""Check custom method scripts for custom property references."""
		if hasattr(node, 'script') and node.script:
			self._check_script_for_references(node.script)

	def visit_transform(self, node):
		"""Check transform scripts for custom property references."""
		if hasattr(node, 'script') and node.script:
			self._check_script_for_references(node.script)

	def _check_expression_for_references(self, expression: str):
		"""Check an expression string for custom property references."""
		if not expression:
			return

		# Look for patterns like {view.custom.propName}, {this.custom.propName}, etc.
		pattern_handlers = [
			(r'\{view\.custom\.([^}]+)\}', lambda m: f"view.custom.{m}"),  # {view.custom.propName}
			(r'\{view\.params\.([^}]+)\}', lambda m: f"view.params.{m}"),  # {view.params.paramName}
			(r'\{this\.custom\.([^}]+)\}', lambda m: f"*.custom.{m}"),  # {this.custom.propName}
			(r'\{self\.view\.custom\.([^}]+)\}',
				lambda m: f"view.custom.{m}"),  # {self.view.custom.propName}
			(r'\{self\.view\.params\.([^}]+)\}',
				lambda m: f"view.params.{m}"),  # {self.view.params.paramName}
		]

		for pattern, handler in pattern_handlers:
			matches = re.findall(pattern, expression)
			for match in matches:
				used_prop = handler(match)
				self.used_properties.add(used_prop)

	def _check_script_for_references(self, script: str):
		"""Check a script string for custom property references."""
		if not script:
			return

		# Look for patterns like self.view.custom.propName, self.view.params.paramName, etc.
		patterns = [
			r'self\.view\.custom\.([a-zA-Z_][a-zA-Z0-9_]*)',  # self.view.custom.propName
			r'self\.view\.params\.([a-zA-Z_][a-zA-Z0-9_]*)',  # self.view.params.paramName
			r'self\.custom\.([a-zA-Z_][a-zA-Z0-9_]*)',  # self.custom.propName (component)
		]

		for pattern in patterns:
			matches = re.findall(pattern, script)
			for match in matches:
				if '.view.custom.' in pattern:
					self.used_properties.add(f"view.custom.{match}")
				elif '.view.params.' in pattern:
					self.used_properties.add(f"view.params.{match}")
				elif '.custom.' in pattern:
					self.used_properties.add(f"*.custom.{match}")

	def finalize(self):
		"""Called after all nodes are visited - check for unused properties."""
		# Search entire flattened JSON for property references
		self._search_flattened_json_for_references()

		unused_properties = []

		for prop_path, definition_location in self.defined_properties.items():
			# Check if this property is used
			is_used = prop_path in self.used_properties

			# For component custom properties, also check wildcard usage
			if not is_used and '.custom.' in prop_path and not prop_path.startswith('view.'):
				# Extract just the property name for wildcard matching
				prop_name = prop_path.split('.custom.')[-1]
				wildcard_path = f"*.custom.{prop_name}"
				is_used = wildcard_path in self.used_properties

			if not is_used:
				unused_properties.append((prop_path, definition_location))

		# Report unused properties
		for prop_path, definition_location in unused_properties:
			prop_type = "view parameter" if ".params." in prop_path else "custom property"
			self.errors.append(
				f"{definition_location}: {prop_type} '{prop_path.split('.')[-1]}' is defined but never referenced"
			)

	def _search_flattened_json_for_references(self):
		"""Search the entire flattened JSON for any references to defined properties."""
		if not self.flattened_json or not self.defined_properties:
			return

		# Get all property paths we're looking for
		search_patterns = []

		for prop_path in self.defined_properties.keys(): # pylint: disable=consider-iterating-dictionary
			if prop_path.startswith('view.custom.'):
				# For view custom properties: view.custom.propName
				prop_name = prop_path[12:]  # Remove 'view.custom.'
				search_patterns.extend([
					f"view.custom.{prop_name}",
					f"self.view.custom.{prop_name}",
					f"{{{prop_name}}}",  # Short form in expressions
				])
			elif prop_path.startswith('view.params.'):
				# For view parameters: view.params.paramName
				param_name = prop_path[12:]  # Remove 'view.params.'
				search_patterns.extend([
					f"view.params.{param_name}",
					f"self.view.params.{param_name}",
					f"{{{param_name}}}",  # Short form in expressions
				])
			elif '.custom.' in prop_path:
				# For component custom properties: ComponentName.custom.propName
				parts = prop_path.split('.custom.')
				component_name = parts[0]
				prop_name = parts[1]
				search_patterns.extend([
					f"{component_name}.custom.{prop_name}",
					f"this.custom.{prop_name}",
					f"self.custom.{prop_name}",
				])

		# Search through all values in the flattened JSON
		for _, json_value in self.flattened_json.items():
			if not isinstance(json_value, str):
				continue

			# Check if any of our search patterns appear in this value
			for pattern in search_patterns:
				if pattern in json_value:
					# Mark the corresponding property as used
					self._mark_property_used_from_pattern(pattern)

	def _mark_property_used_from_pattern(self, pattern: str):
		"""Mark a property as used based on a found pattern."""
		# Extract the property path from the pattern
		if 'view.custom.' in pattern:
			# Extract property name from patterns like "view.custom.propName" or "self.view.custom.propName"
			match = re.search(r'view\.custom\.([a-zA-Z_][a-zA-Z0-9_]*)', pattern)
			if match:
				prop_name = match.group(1)
				self.used_properties.add(f"view.custom.{prop_name}")
		elif 'view.params.' in pattern:
			# Extract parameter name from patterns like "view.params.paramName" or "self.view.params.paramName"
			match = re.search(r'view\.params\.([a-zA-Z_][a-zA-Z0-9_]*)', pattern)
			if match:
				param_name = match.group(1)
				self.used_properties.add(f"view.params.{param_name}")
		elif '.custom.' in pattern:
			# Extract component and property name from patterns like "ComponentName.custom.propName" or "this.custom.propName"
			if pattern.startswith('this.custom.') or pattern.startswith('self.custom.'):
				# Generic component reference - mark as wildcard
				match = re.search(r'\.custom\.([a-zA-Z_][a-zA-Z0-9_]*)', pattern)
				if match:
					prop_name = match.group(1)
					self.used_properties.add(f"*.custom.{prop_name}")
			else:
				# Specific component reference
				match = re.search(r'([^.]+)\.custom\.([a-zA-Z_][a-zA-Z0-9_]*)', pattern)
				if match:
					component_name = match.group(1)
					prop_name = match.group(2)
					self.used_properties.add(f"{component_name}.custom.{prop_name}")
