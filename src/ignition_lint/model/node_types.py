from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import re


# Base classes for our object model
class ViewNode(ABC):
	"""Base class for all nodes in the view tree."""

	def __init__(self, path: str, value: Any):
		self.path = path
		self.value = value

	@abstractmethod
	def accept(self, visitor):
		"""Accept a visitor that will process this node."""
		pass


# Specific node types for different view elements
class Component(ViewNode):
	"""Represents a component in the view."""

	def __init__(self, path: str, name: str, type_name: str = None, properties: Dict = None):
		super().__init__(path, None)
		self.name = name
		self.type = type_name
		self.properties = properties or {}
		self.children = []

	def accept(self, visitor):
		return visitor.visit_component(self)


class Binding(ViewNode):
	"""Represents a binding in the view."""

	def __init__(self, path: str, binding_type: str, config: Dict = None):
		super().__init__(path, None)
		self.binding_type = binding_type
		self.config = config or {}

	def accept(self, visitor):
		return visitor.visit_binding(self)


class ExpressionBinding(Binding):
	"""Represents an expression binding in the view."""

	def __init__(self, path: str, expression: str, config: Dict = None):
		super().__init__(path, "expr", config)
		self.expression = expression

	def accept(self, visitor):
		return visitor.visit_expression_binding(self)


class PropertyBinding(Binding):
	"""Represents a property binding in the view."""

	def __init__(self, path: str, target_path: str, config: Dict = None):
		super().__init__(path, "property", config)
		self.target_path = target_path

	def accept(self, visitor):
		return visitor.visit_property_binding(self)


class TagBinding(Binding):
	"""Represents a tag binding in the view."""

	def __init__(self, path: str, tag_path: str, config: Dict = None):
		super().__init__(path, "tag", config)
		self.tag_path = tag_path

	def accept(self, visitor):
		return visitor.visit_tag_binding(self)


class Script(ViewNode):
	"""Represents a script in the view."""

	def __init__(self, path: str, code: str, script_type: str = None):
		super().__init__(path, code)
		self.code = code
		self.script_type = script_type  # e.g., "transform", "customMethod", "messageHandler"

	def accept(self, visitor):
		return visitor.visit_script(self)


class MessageHandler(Script):
	"""Represents a message handler in the view."""

	def __init__(self, path: str, code: str, message_type: str, scope: Dict = None):
		super().__init__(path, code, "messageHandler")
		self.message_type = message_type
		self.scope = scope or {}

	def get_formatted_code(self):
		"""Format the script with the proper function definition for pylint."""
		# Message handlers typically receive a payload parameter
		function_def = f"def onMessageReceived(self, payload):"

		# Indent the code properly
		indented_code = "\n".join(f"{line}" for line in self.code.split("\n"))

		# Combine into a complete function
		return f"{function_def}\n{indented_code}"

	def accept(self, visitor):
		return visitor.visit_message_handler(self)


class CustomMethodScript(Script):
	"""Represents a custom method in the view."""

	def __init__(self, path: str, name: str, code: str, params=None):
		super().__init__(path, code, "customMethod")
		self.name = name
		self.params = params or []

	def get_formatted_code(self):
		"""Format the script with the proper function definition for pylint."""
		# Create function signature with self and all params
		param_list = ", ".join(["self"] + self.params)
		function_def = f"def {self.name}({param_list}):"

		# Indent the code properly
		indented_code = "\n".join(f"{line}" for line in self.code.split("\n"))

		# Handle empty function body case
		if not indented_code.strip():
			indented_code = "    pass"

		# Combine into a complete function
		full_code = f"{function_def}\n{indented_code}"

		return full_code

	def accept(self, visitor):
		return visitor.visit_custom_method(self)


class TransformScript(Script):
	"""Represents a script transform in a binding."""

	def __init__(self, path: str, code: str, binding_path: str = None):
		super().__init__(path, code, "transform")
		self.binding_path = binding_path

	def get_formatted_code(self):
		"""Format the script with the proper function definition for pylint."""
		# Transforms typically receive a value parameter
		function_def = "def transform(self, value):"

		# Indent the code properly
		indented_code = "\n".join(f"{line}" for line in self.code.split("\n"))

		# Combine into a complete function
		return f"{function_def}\n{indented_code}"

	def accept(self, visitor):
		return visitor.visit_script_transform(self)


class EventHandler(ViewNode):
	"""Represents an event handler in the view."""

	def __init__(self, path: str, event_type: str, handler_type: str, config: Dict = None):
		super().__init__(path, None)
		self.event_type = event_type  # e.g., "onClick"
		self.handler_type = handler_type  # e.g., "script", "openPage"
		self.config = config or {}

	def accept(self, visitor):
		return visitor.visit_event_handler(self)


class EventHandlerScript(EventHandler):
	"""Represents a script event handler in the view."""

	def __init__(self, path: str, event_type: str, code: str, scope: str = None):
		super().__init__(path, event_type, "script")
		self.code = code
		self.scope = scope

	def get_formatted_code(self):
		"""Format the script with the proper function definition for pylint."""
		# Create a sanitized function name from the event type
		function_def = f"def {self.event_type}(self, event):"

		# Indent the code properly
		indented_code = "\n".join(f"{line}" for line in self.code.split("\n"))

		# Handle empty function body case
		if not indented_code.strip():
			indented_code = "    pass"

		# Combine into a complete function
		return f"{function_def}\n{indented_code}"

	def accept(self, visitor):
		return visitor.visit_script_event_handler(self)


class Property(ViewNode):
	"""Represents a property of a component."""

	def __init__(self, path: str, name: str, value: Any):
		super().__init__(path, value)
		self.name = name

	def accept(self, visitor):
		return visitor.visit_property(self)
