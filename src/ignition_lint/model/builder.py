import re
from .node_types import *
from typing import Dict, List, Any, Optional, Union


class ViewModelBuilder:
	"""Builds a structured view model from flattened JSON."""

	def _get_component_type(self, data: Dict[str, Any], component_path: str) -> str:
		"""Get the type of a component."""
		type_path = f"{component_path}.type"
		return data.get(type_path, "unknown")

	def _get_expression(self, data: Dict[str, Any], binding_path: str) -> str:
		"""Get the expression from an expression binding."""
		expr_path = f"{binding_path}.binding.config.expression"
		return data.get(expr_path, "")

	def _get_property_path(self, data: Dict[str, Any], binding_path: str) -> str:
		"""Get the target path from a property binding."""
		path_path = f"{binding_path}.config.path"
		return data.get(path_path, "")

	def _get_tag_path(self, data: Dict[str, Any], binding_path: str) -> str:
		"""Get the tag path from a tag binding."""
		tag_path = f"{binding_path}.config.tagPath"
		return data.get(tag_path, "")

	def _get_script_transforms(self, data: Dict[str, Any], binding_path: str) -> List[tuple]:
		"""Get script transforms from a binding."""
		transforms = []
		transform_paths = []

		# Find transform paths
		for path in data:
			if path.startswith(f"{binding_path}.transforms") and path.endswith('.type'):
				if data[path] == 'script':
					transform_base = path.rsplit('.type', 1)[0]
					transform_paths.append(transform_base)

		# Get transform script for each path
		for transform_path in transform_paths:
			script_path = f"{transform_path}.script"
			if script_path in data:
				transforms.append((transform_path, data[script_path]))

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

	def build_model(self, flattened_json: Dict[str, Any]) -> Dict[str, List[ViewNode]]:
		"""
		Parse the flattened JSON and build a structured model.
		
		Returns:
			Dict mapping node types to lists of those nodes
		"""
		# Initialize collections for each node type
		model = {
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

		# First, identify components by looking for meta.name entries
		components = {}
		for path, value in flattened_json.items():
			if not path.endswith('.meta.name'):
				continue
			component_path = path.rsplit('.meta.name', 1)[0]
			component_name = value
			component_type = self._get_component_type(flattened_json, component_path)
			components[component_path] = Component(component_path, component_name, component_type)
			model['components'].append(components[component_path])

		# Process bindings
		visited_paths = []
		for path, binding_type in flattened_json.items():
			if '.binding.type' not in path:
				continue
			binding_path = path.rsplit('.binding.type', 1)[0]
			if binding_path not in visited_paths:
				visited_paths.append(binding_path)

				if binding_type == 'expr':
					expression = self._get_expression(flattened_json, binding_path)
					binding = ExpressionBinding(binding_path, expression)
					model['expression_bindings'].append(binding)
					model['bindings'].append(binding)

				elif binding_type == 'property':
					target_path = self._get_property_path(flattened_json, binding_path)
					binding = PropertyBinding(binding_path, target_path)
					model['property_bindings'].append(binding)
					model['bindings'].append(binding)

				elif binding_type == 'tag':
					tag_path = self._get_tag_path(flattened_json, binding_path)
					binding = TagBinding(binding_path, tag_path)
					model['tag_bindings'].append(binding)
					model['bindings'].append(binding)

				# Look for script transforms in the binding
				transforms = self._get_script_transforms(flattened_json, binding_path)
				for transform_path, script in transforms:
					transform = TransformScript(transform_path, script, binding_path)
					model['script_transforms'].append(transform)
					model['scripts'].append(transform)

		# Process message handlers
		for path, message_type in flattened_json.items():
			if '.scripts.messageHandlers' in path and path.endswith('.messageType'):
				base_path = path.rsplit('.messageType', 1)[0]
				script_path = f"{base_path}.script"
				script_code = flattened_json.get(script_path, "")

				# Get scope information
				scope = {
					'page': flattened_json.get(f"{base_path}.pageScope", False),
					'session': flattened_json.get(f"{base_path}.sessionScope", False),
					'view': flattened_json.get(f"{base_path}.viewScope", False)
				}

				handler = MessageHandlerScript(base_path, script_code, message_type, scope)
				model['message_handlers'].append(handler)
				model['scripts'].append(handler)

		# Process custom methods
		custom_method_data = {}
		# First, collect all the data for each custom method
		for path, value in flattened_json.items():
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
			model['custom_methods'].append(method)
			model['scripts'].append(method)

		# Process event handlers
		for path, script in flattened_json.items():
			# Look for event handler script configurations
			if '.events.' in path and '.config.script' in path:
				# Extract the event path components
				event_path_parts = path.split('.config.script')[0]
				event_path = event_path_parts

				# Extract event domain and type from path
				domain_type_match = re.search(r'\.events\.([^.]+)\.([^.]+)', event_path_parts)
				if domain_type_match:
					event_domain = domain_type_match.group(1)  # e.g., 'dom', 'system'
					event_type = domain_type_match.group(2)  # e.g., 'onClick', 'onStartup'

					# Get the scope if available
					scope_path = f"{event_path}.scope"
					scope = flattened_json.get(scope_path, "L")  # Default to local scope

					# Create a script event handler
					handler = EventHandlerScript(event_path, event_type, script, scope)
					model['event_handlers'].append(handler)
					model['scripts'].append(handler)

		# Process regular properties
		for path, value in flattened_json.items():
			# Skip meta properties, bindings, scripts - we already processed those
			processed_paths = ['.meta.', '.binding.', '.scripts.', '.events.']
			if (not any(x in path for x in processed_paths) and not path.endswith('.type')):

				# Find the component this property belongs to
				component_path = None
				for comp_path in components:
					if path.startswith(comp_path):
						# Take the longest matching path (most specific component)
						if component_path is None or len(comp_path) > len(component_path):
							component_path = comp_path

				if component_path:
					property_name = path.replace(f"{component_path}.", "")
					prop = Property(path, property_name, value)
					model['properties'].append(prop)
					# Add the property to the component
					if component_path in components:
						components[component_path].properties[property_name] = value

		return model
