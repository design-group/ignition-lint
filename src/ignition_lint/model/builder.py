"""
This module defines the ViewModelBuilder class, which constructs a structured view model
from a flattened JSON representation of an Ignition Perspective view. It includes methods to extract
component types, bindings, event handlers, and other elements from the JSON data.
"""
import re
from typing import Dict, List, Any

from .node_types import (
	ViewNode,
	Component,
	ExpressionBinding,
	PropertyBinding,
	TagBinding,
	MessageHandlerScript,
	CustomMethodScript,
	TransformScript,
	EventHandlerScript,
	Property,
)


class ViewModelBuilder:
	"""Builds a structured view model from flattened JSON."""

	def __init__(self):
		self.flattened_json = {}
		self.model = {
			'components': [],
			'bindings': [],
			'scripts': [],
			'event_handlers': [],
			'message_handlers': [],
			'custom_methods': [],
			'expression_bindings': [],
			'property_bindings': [],
			'tag_bindings': [],
			'script_transforms': [],
			'properties': []
		}

	def _search_for_path_value(self, path: str, suffix: str = None, fallback: Any = None) -> Any:
		"""Search for a value in the flattened JSON by path, optionally with a suffix."""
		full_path = f"{path}.{suffix}" if suffix else path
		return self.flattened_json.get(full_path, fallback)

	def _get_component_type(self, component_path: str) -> str:
		"""Get the type of a component."""
		return self._search_for_path_value(component_path, "type", "unknown")

	def _get_expression(self, binding_path: str) -> str:
		"""Get the expression from an expression binding."""
		return self._search_for_path_value(binding_path, "binding.config.expression", "unknown")

	def _get_property_path(self, binding_path: str) -> str:
		"""Get the target path from a property binding."""
		return self._search_for_path_value(binding_path, "binding.config.path", "unknown")

	def _get_tag_path(self, binding_path: str) -> str:
		"""Get the tag path from a tag binding."""
		return self._search_for_path_value(binding_path, "binding.config.tagPath", "unknown")

	def _get_script_transforms(self, binding_path: str) -> List[tuple]:
		"""Get script transforms from a binding."""
		transforms = []
		transform_paths = []

		# Find transform paths
		for path, value in self.flattened_json.items():
			if path.startswith(f"{binding_path}.transforms"
						) and path.endswith('.type') and value == 'script':
				transform_base = path.rsplit('.type', 1)[0]
				transform_paths.append(transform_base)

		# Get transform script for each path
		for transform_path in transform_paths:
			script_path = f"{transform_path}.script"
			if script_path in self.flattened_json:
				transforms.append((transform_path, self.flattened_json[script_path]))

		return transforms

	def _extract_event_type(self, handler_path: str) -> str:
		"""Extract the event type from an event handler path."""
		# Example: path.events.dom.onClick.type -> onClick
		parts = handler_path.split('.')
		for i, part in enumerate(parts):
			if part == 'events' and i + 2 < len(parts):
				return parts[i + 2]
		return "unknown"

	def _extract_config(self, data: Dict[str, Any], config_path: str) -> Dict:
		"""Extract configuration for a component."""
		config = {}
		prefix = f"{config_path}."
		for path, value in data.items():
			if path.startswith(prefix):
				key = path[len(prefix):]
				config[key] = value
		return config

	def _is_property_persistent(self, property_path: str) -> bool:
		"""
		Check if a property is persistent (exists at startup) or non-persistent (created by bindings).
		
		Properties are considered persistent if:
		1. They have no propConfig entry (default behavior)
		2. They have propConfig.{property_path}.persistent = True
		
		Args:
			property_path: The path to the property (e.g., "custom.myProp" or "root.root.children[0].Button.custom.myProp")
		
		Returns:
			True if the property should be persistent, False if it's created by bindings at runtime
		"""
		# Check for explicit persistence configuration
		config_path = f"propConfig.{property_path}.persistent"
		persistent_value = self.flattened_json.get(config_path)

		if persistent_value is not None:
			# Explicit configuration found
			return persistent_value

		# No explicit configuration - check if there's any propConfig for this property
		config_prefix = f"propConfig.{property_path}."
		has_any_config = any(path.startswith(config_prefix) for path in self.flattened_json.keys())

		if has_any_config:
			# Property has configuration but no explicit persistent setting
			# Default to True (persistent) unless proven otherwise
			return True

		# No configuration at all - default to persistent
		return True

	def _collect_components(self):
		# First, identify components by looking for meta.name entries
		for path, value in self.flattened_json.items():
			if not path.endswith('.meta.name'):
				continue
			component_path = path.rsplit('.meta.name', 1)[0]
			component_name = value
			component_type = self._get_component_type(component_path)
			self.model['components'].append(Component(component_path, component_name, component_type))

	def _collect_bindings(self):
		"""Collect all bindings from the flattened JSON."""
		visited_paths = []
		for path, binding_type in self.flattened_json.items():
			if '.binding.type' not in path:
				continue
			binding_path = path.rsplit('.binding.type', 1)[0]
			if binding_path not in visited_paths:
				visited_paths.append(binding_path)

				if binding_type in ('expression', 'expr'):
					expression = self._get_expression(binding_path)
					binding = ExpressionBinding(binding_path, expression)
					self.model['expression_bindings'].append(binding)
					self.model['bindings'].append(binding)

				elif binding_type == 'property':
					target_path = self._get_property_path(binding_path)
					binding = PropertyBinding(binding_path, target_path)
					self.model['property_bindings'].append(binding)
					self.model['bindings'].append(binding)

				elif binding_type == 'tag':
					tag_path = self._get_tag_path(binding_path)
					binding = TagBinding(binding_path, tag_path)
					self.model['tag_bindings'].append(binding)
					self.model['bindings'].append(binding)

				# Look for script transforms in the binding
				full_binding_path = f"{binding_path}.binding"
				transforms = self._get_script_transforms(full_binding_path)
				for transform_path, script in transforms:
					transform = TransformScript(transform_path, script, binding_path)
					self.model['script_transforms'].append(transform)
					self.model['scripts'].append(transform)

	def _collect_message_handlers(self):
		"""Collect all message handlers from the flattened JSON."""
		for path, message_type in self.flattened_json.items():
			if '.scripts.messageHandlers' in path and path.endswith('.messageType'):
				base_path = path.rsplit('.messageType', 1)[0]
				script_code = self._search_for_path_value(base_path, "script", "")

				# Get scope information
				scope = {
					'page': self._search_for_path_value(base_path, "pageScope", False),
					'session': self._search_for_path_value(base_path, "sessionScope", False),
					'view': self._search_for_path_value(base_path, "viewScope", False)
				}

				handler = MessageHandlerScript(base_path, script_code, message_type, scope)
				self.model['message_handlers'].append(handler)
				self.model['scripts'].append(handler)

	def _collect_custom_methods(self):
		"""Collect all custom methods from the flattened JSON."""
		custom_method_data = {}
		# First, collect all the data for each custom method
		for path, value in self.flattened_json.items():
			if '.scripts.customMethods' not in path:
				continue
			# Extract the method index
			match = re.search(r'\.scripts\.customMethods\[(\d+)\]', path)
			if match:
				method_index = int(match.group(1))
				component_path = path.split('.scripts.customMethods')[0]
				method_id = f"{component_path}.customMethod_{method_index}"

				# Initialize this method's data if needed
				if method_id not in custom_method_data:
					custom_method_data[method_id] = {
						'path': f"{component_path}.scripts.customMethods[{method_index}]",
						'name': 'unknown_method',
						'params': [],
						'script': ''
					}

				# Check what type of data this is
				if path.endswith('.name'):
					custom_method_data[method_id]['name'] = value
				elif path.endswith('.script'):
					custom_method_data[method_id]['script'] = value
				elif 'params' in path:
					# Extract parameter index
					param_match = re.search(r'params\[(\d+)\]', path)
					if param_match:
						param_index = int(param_match.group(1))
						# Ensure params list is long enough
						while len(custom_method_data[method_id]['params']) <= param_index:
							custom_method_data[method_id]['params'].append('')
						# Set parameter at correct index
						custom_method_data[method_id]['params'][param_index] = value

		# Now create CustomMethodScript objects from the collected data
		for method_id, data in custom_method_data.items():
			method = CustomMethodScript(data['path'], data['name'], data['script'], data['params'])
			self.model['custom_methods'].append(method)
			self.model['scripts'].append(method)

	def _collect_event_handlers(self):
		"""Collect all event handlers from the flattened JSON."""
		for path, script in self.flattened_json.items():
			# Look for event handler script configurations
			# Check both .config.script (alternative format) and .script (standard format)
			if '.events.' in path and ('.config.script' in path or path.endswith('.script')):
				if '.config.script' in path:
					# Alternative format: path.events.eventType.config.script
					event_path_parts = path.split('.config.script')[0]
				else:
					# Standard format: path.events.eventType.script
					event_path_parts = path.split('.script')[0]
				
				event_path = event_path_parts

				# Extract event type from path (e.g., 'onActionPerformed', 'onStartup')
				# Standard Ignition events don't use domains, just event types
				event_type_match = re.search(r'\.events\.([^.]+)$', event_path_parts)
				if event_type_match:
					event_type = event_type_match.group(1)  # e.g., 'onActionPerformed', 'onStartup'
					
					# Get the scope from the same event path
					scope_path = f"{event_path_parts}.scope"
					scope = self.flattened_json.get(scope_path, "L")

					# Create a script event handler
					handler = EventHandlerScript(
						event_path, "component", event_type, script, scope=scope
					)
					self.model['event_handlers'].append(handler)
					self.model['scripts'].append(handler)

	def _collect_properties(self):
		for path, value in self.flattened_json.items():
			# Skip meta properties, bindings, scripts, events - we already processed those
			processed_props = ['meta', 'binding', 'scripts', 'events']
			if any(f".{prop}." in path for prop in processed_props) or path.endswith('.type'):
				continue

			# Skip propConfig properties - these are configuration, not actual properties
			if path.startswith('propConfig.'):
				continue

			# Handle view-level properties (custom.* and params.*)
			if path.startswith('custom.') or path.startswith('params.'):
				# Check if this is a persistent property
				if self._is_property_persistent(path):
					property_name = path.split(".")[-1]
					prop = Property(path, property_name, value)
					self.model['properties'].append(prop)
				continue

			# Find the component this property belongs to
			component_path = None
			for comp_obj in self.model['components']:
				if path.startswith(comp_obj.path):
					# Take the longest matching path (most specific component)
					if component_path is None or len(comp_obj.path) > len(component_path):
						component_path = comp_obj.path

			if component_path:
				# For component properties, also check persistence for custom properties
				if '.custom.' in path and not self._is_property_persistent(path):
					continue

				property_name = path.split(".")[-1]

				prop = Property(path, property_name, value)
				self.model['properties'].append(prop)
				# Add the property to the component
				if component_path in self.model['components']:
					self.model['components'][component_path].properties[property_name] = value

	def get_view_model(self) -> Dict[str, List[ViewNode]]:
		"""Return the structured view model."""
		return self.model

	def build_model(self, flattened_json: Dict[str, Any]) -> Dict[str, List[ViewNode]]:
		"""
		Parse the flattened JSON and build a structured model.

		Returns:
			Dict mapping node types to lists of those nodes
		"""
		self.flattened_json = flattened_json

		# Reset model to avoid accumulation from multiple calls
		self.model = {
			'components': [],
			'bindings': [],
			'scripts': [],
			'event_handlers': [],
			'message_handlers': [],
			'custom_methods': [],
			'expression_bindings': [],
			'property_bindings': [],
			'tag_bindings': [],
			'script_transforms': [],
			'properties': []
		}

		# First, identify components
		self._collect_components()

		# Process bindings
		self._collect_bindings()

		# Process message handlers
		self._collect_message_handlers()

		# Process custom methods
		self._collect_custom_methods()

		# Process event handlers
		self._collect_event_handlers()

		# Process regular properties
		self._collect_properties()

		return self.get_view_model()
