"""
This rule checks component naming conventions in Ignition Perspective views.
Supports predefined naming conventions and custom regex patterns.
"""
import re
from typing import Dict, Optional
from .common import LintingRule
from ..model.node_types import ViewNode, NodeType


class ComponentNameRule(LintingRule):
	"""Rule that checks component naming conventions with flexible patterns."""

	# Predefined naming convention patterns
	NAMING_CONVENTIONS = {
		'PascalCase': {
			'pattern': r'^[A-Z][a-zA-Z0-9]*$',
			'description': 'PascalCase (e.g., MyButton, DataTable)',
			'examples': ['Button1', 'DataTable', 'MyCustomComponent'],
			'invalid_examples': ['button1', 'data_table', 'my-component']
		},
		'camelCase': {
			'pattern': r'^[a-z][a-zA-Z0-9]*$',
			'description': 'camelCase (e.g., myButton, dataTable)',
			'examples': ['button1', 'dataTable', 'myCustomComponent'],
			'invalid_examples': ['Button1', 'data_table', 'my-component']
		},
		'snake_case': {
			'pattern': r'^[a-z][a-z0-9_]*$',
			'description': 'snake_case (e.g., my_button, data_table)',
			'examples': ['button_1', 'data_table', 'my_custom_component'],
			'invalid_examples': ['Button1', 'dataTable', 'my-component']
		},
		'kebab-case': {
			'pattern': r'^[a-z][a-z0-9-]*$',
			'description': 'kebab-case (e.g., my-button, data-table)',
			'examples': ['button-1', 'data-table', 'my-custom-component'],
			'invalid_examples': ['Button1', 'dataTable', 'my_component']
		},
		'SCREAMING_SNAKE_CASE': {
			'pattern': r'^[A-Z][A-Z0-9_]*$',
			'description': 'SCREAMING_SNAKE_CASE (e.g., MY_BUTTON, DATA_TABLE)',
			'examples': ['BUTTON_1', 'DATA_TABLE', 'MY_CUSTOM_COMPONENT'],
			'invalid_examples': ['Button1', 'dataTable', 'my-component']
		},
		'Title Case': {
			'pattern': r'^[A-Z][a-z]*(\s[A-Z][a-z]*)*$',
			'description': 'Title Case with spaces (e.g., My Button, Data Table)',
			'examples': ['Button One', 'Data Table', 'My Custom Component'],
			'invalid_examples': ['button one', 'dataTable', 'my-component']
		},
		'lower case': {
			'pattern': r'^[a-z][a-z\s]*$',
			'description': 'lower case with spaces (e.g., my button, data table)',
			'examples': ['button one', 'data table', 'my custom component'],
			'invalid_examples': ['Button One', 'dataTable', 'my-component']
		}
	}

	def __init__(
		self,
		convention: Optional[str] = None,
		custom_pattern: Optional[str] = None,
		allow_numbers: bool = True,
		min_length: int = 1,
		max_length: Optional[int] = None,
		forbidden_names: Optional[list] = None,
		allowed_abbreviations: Optional[list] = None,
		auto_detect_abbreviations: bool = True,
	):
		"""
        Initialize the component naming rule.
        
        Args:
            convention: Predefined naming convention (PascalCase, camelCase, snake_case, etc.)
            custom_pattern: Custom regex pattern (overrides convention)
            allow_numbers: Whether to allow numbers in component names
            min_length: Minimum length for component names
            max_length: Maximum length for component names (None for no limit)
            forbidden_names: List of forbidden component names
            allowed_abbreviations: List of allowed abbreviations/acronyms (e.g., ['FBI', 'XML', 'HTTP'])
            auto_detect_abbreviations: Whether to automatically detect common abbreviations
        """
		super().__init__({NodeType.COMPONENT})

		self.convention = convention
		self.custom_pattern = custom_pattern
		self.allow_numbers = allow_numbers
		self.min_length = min_length
		self.max_length = max_length
		self.forbidden_names = set(forbidden_names or [])
		self.allowed_abbreviations = set(allowed_abbreviations or [])
		self.auto_detect_abbreviations = auto_detect_abbreviations

		# Common abbreviations that are often used in programming
		self.common_abbreviations = {
			'API', 'HTTP', 'HTTPS', 'XML', 'JSON', 'SQL', 'URL', 'URI', 'UUID', 'CPU', 'GPU', 'RAM', 'SSD',
			'HDD', 'PDF', 'CSV', 'ZIP', 'GIF', 'PNG', 'JPG', 'JPEG', 'SVG', 'CSS', 'HTML', 'JS', 'TS',
			'PHP', 'ASP', 'JSP', 'CGI', 'FTP', 'SSH', 'TCP', 'UDP', 'IP', 'DNS', 'DHCP', 'VPN', 'SSL',
			'TLS', 'JWT', 'CRUD', 'REST', 'SOAP', 'AJAX', 'DOM', 'UI', 'UX', 'GUI', 'CLI', 'OS', 'iOS',
			'macOS', 'AWS', 'GCP', 'IBM', 'AI', 'ML', 'NLP', 'OCR', 'QR', 'RFID', 'NFC', 'GPS', 'LED',
			'LCD', 'OLED', 'CRT', 'ID'
		}

		self.skip_names = {'root'}

		# Combine user-provided and common abbreviations
		if self.auto_detect_abbreviations:
			self.all_abbreviations = self.allowed_abbreviations | self.common_abbreviations
		else:
			self.all_abbreviations = self.allowed_abbreviations

		# Determine the pattern to use
		if custom_pattern:
			self.pattern = custom_pattern
			self.pattern_description = f"custom pattern: {custom_pattern}"
		elif convention and convention in self.NAMING_CONVENTIONS:
			conv_info = self.NAMING_CONVENTIONS[convention]
			base_pattern = conv_info['pattern']

			# Modify pattern based on allow_numbers setting
			if not allow_numbers:
				# Remove number support from the pattern
				base_pattern = base_pattern.replace('0-9', '')

			self.pattern = base_pattern
			self.pattern_description = conv_info['description']
		else:
			# Default to PascalCase
			self.pattern = self.NAMING_CONVENTIONS['PascalCase']['pattern']
			self.pattern_description = self.NAMING_CONVENTIONS['PascalCase']['description']
			if convention:
				print(f"Warning: Unknown convention '{convention}', using PascalCase as default")

	@property
	def error_message(self) -> str:
		return f"Component name should follow {self.pattern_description}"

	def visit_component(self, node: ViewNode):
		"""Check if component name follows the naming convention."""
		name = node.name

		# Skip validation for root or other predefined names
		if name in self.skip_names:
			return

		# Check forbidden names first
		if name in self.forbidden_names:
			self.errors.append(f"{node.path}: Component name '{name}' is forbidden")
			return

		# Check length constraints
		if len(name) < self.min_length:
			self.errors.append(
				f"{node.path}: Component name '{name}' is too short (minimum {self.min_length} characters)"
			)
			return

		if self.max_length and len(name) > self.max_length:
			self.errors.append(
				f"{node.path}: Component name '{name}' is too long (maximum {self.max_length} characters)"
			)
			return

		# Check if name contains abbreviations and handle them
		processed_name = self._process_abbreviations(name)

		# Check pattern on the processed name
		if not re.match(self.pattern, processed_name):
			error_msg = f"{node.path}: Component name '{name}' doesn't follow {self.pattern_description}"

			# Add helpful suggestions if using a predefined convention
			if self.convention and self.convention in self.NAMING_CONVENTIONS:
				conv_info = self.NAMING_CONVENTIONS[self.convention]
				if conv_info.get('examples'):
					suggestion = self._suggest_name(name)
					if suggestion:
						error_msg += f" (suggestion: '{suggestion}')"

			self.errors.append(error_msg)

	def _process_abbreviations(self, name: str) -> str:
		"""
        Process a name to handle abbreviations according to the naming convention.
        Returns a version of the name that should pass pattern matching.
        """
		if not self.all_abbreviations:
			return name

		# For custom patterns, don't modify the name
		if self.custom_pattern:
			return name

		processed_name = name

		# Find abbreviations in the name and adjust them based on convention
		for abbrev in sorted(self.all_abbreviations, key=len, reverse=True):  # Longest first
			if abbrev in name.upper():
				if self.convention in ['PascalCase', 'camelCase']:
					# For PascalCase and camelCase, abbreviations should be all caps
					# Examples: XMLParser, HTTPSConnection, parseXMLData
					processed_name = self._adjust_abbreviation_for_camel_case(
						processed_name, abbrev
					)
				elif self.convention in ['snake_case', 'kebab-case']:
					# For snake_case or kebab-case, abbreviations become lowercase
					# Examples: xml_parser, https_connection, parse_xml_data
					processed_name = processed_name.replace(abbrev.upper(), abbrev.lower())
					processed_name = processed_name.replace(abbrev.lower(), abbrev.lower())
				elif self.convention == 'SCREAMING_SNAKE_CASE':
					# For SCREAMING_SNAKE_CASE, everything is uppercase anyway
					processed_name = processed_name.upper()
				elif self.convention in ['Title Case', 'lower case']:
					# For Title Case and lower case, treat abbreviations as regular words
					if self.convention == 'Title Case':
						# FBI Agent -> FBI Agent (keep abbreviation uppercase)
						processed_name = self._adjust_abbreviation_for_title_case(
							processed_name, abbrev
						)
					else:
						# fbi agent -> fbi agent (lowercase)
						processed_name = processed_name.lower()

		return processed_name

	def _adjust_abbreviation_for_camel_case(self, name: str, abbrev: str) -> str:
		"""Adjust abbreviations in camelCase/PascalCase names."""
		# Handle various forms the abbreviation might appear in
		variations = [
			abbrev.upper(),  # XML
			abbrev.lower(),  # xml
			abbrev.capitalize(),  # Xml
		]

		for variation in variations:
			if variation in name:
				# Replace with the uppercase version
				name = name.replace(variation, abbrev.upper())

		return name

	def _adjust_abbreviation_for_title_case(self, name: str, abbrev: str) -> str:
		"""Adjust abbreviations in Title Case names."""
		# In Title Case, keep abbreviations uppercase
		# "Fbi Agent" -> "FBI Agent"
		words = name.split()
		adjusted_words = []

		for word in words:
			if word.upper() == abbrev.upper():
				adjusted_words.append(abbrev.upper())
			else:
				adjusted_words.append(word)

		return ' '.join(adjusted_words)

	def _suggest_name(self, name: str) -> Optional[str]:
		"""Suggest a corrected name based on the current convention."""
		if not self.convention or self.convention not in self.NAMING_CONVENTIONS:
			return None

		# Basic name transformation suggestions
		if self.convention == 'PascalCase':
			# Convert to PascalCase
			return self._to_pascal_case(name)
		elif self.convention == 'camelCase':
			# Convert to camelCase
			return self._to_camel_case(name)
		elif self.convention == 'snake_case':
			# Convert to snake_case
			return self._to_snake_case(name)
		elif self.convention == 'kebab-case':
			# Convert to kebab-case
			return self._to_kebab_case(name)
		elif self.convention == 'SCREAMING_SNAKE_CASE':
			# Convert to SCREAMING_SNAKE_CASE
			return self._to_snake_case(name).upper()
		elif self.convention == 'Title Case':
			# Convert to Title Case
			return self._to_title_case(name)
		elif self.convention == 'lower case':
			# Convert to lower case
			return self._to_lower_case(name)

		return None

	def _to_pascal_case(self, name: str) -> str:
		"""Convert name to PascalCase, preserving abbreviations."""
		# Split on various delimiters
		parts = re.split(r'[-_\s]+', name.lower())
		result_parts = []

		for part in parts:
			if part:
				# Check if this part is an abbreviation
				if part.upper() in self.all_abbreviations:
					result_parts.append(part.upper())
				else:
					result_parts.append(part.capitalize())

		return ''.join(result_parts)

	def _to_camel_case(self, name: str) -> str:
		"""Convert name to camelCase, preserving abbreviations."""
		pascal = self._to_pascal_case(name)
		if not pascal:
			return ""

		# For camelCase, the first part should be lowercase unless it's an abbreviation
		if len(pascal) > 0:
			# Check if the beginning is an abbreviation
			for abbrev in sorted(self.all_abbreviations, key=len, reverse=True):
				if pascal.startswith(abbrev):
					# If it starts with an abbreviation, keep it uppercase
					return pascal

			# Otherwise, lowercase the first character
			return pascal[0].lower() + pascal[1:]

		return pascal

	def _to_snake_case(self, name: str) -> str:
		"""Convert name to snake_case, handling abbreviations."""
		# Handle PascalCase/camelCase, preserving abbreviations
		# First, identify abbreviations and mark them
		temp_name = name
		abbrev_map = {}

		for i, abbrev in enumerate(sorted(self.all_abbreviations, key=len, reverse=True)):
			if abbrev in name.upper():
				placeholder = f"__ABBREV_{i}__"
				temp_name = temp_name.replace(abbrev.upper(), placeholder)
				temp_name = temp_name.replace(abbrev.lower(), placeholder)
				temp_name = temp_name.replace(abbrev.capitalize(), placeholder)
				abbrev_map[placeholder] = abbrev.lower()

		# Convert to snake_case
		temp_name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', temp_name)
		temp_name = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', temp_name)
		temp_name = re.sub(r'[-\s]+', '_', temp_name)
		temp_name = temp_name.lower()

		# Restore abbreviations
		for placeholder, abbrev in abbrev_map.items():
			temp_name = temp_name.replace(placeholder.lower(), abbrev)

		return temp_name

	def _to_kebab_case(self, name: str) -> str:
		"""Convert name to kebab-case, handling abbreviations."""
		return self._to_snake_case(name).replace('_', '-')

	def _to_title_case(self, name: str) -> str:
		"""Convert name to Title Case, preserving abbreviations."""
		# Split on various delimiters
		parts = re.split(r'[-_\s]+', name.lower())
		result_parts = []

		for part in parts:
			if part:
				# Check if this part is an abbreviation
				if part.upper() in self.all_abbreviations:
					result_parts.append(part.upper())
				else:
					result_parts.append(part.capitalize())

		return ' '.join(result_parts)

	def _to_lower_case(self, name: str) -> str:
		"""Convert name to lower case with spaces."""
		return self._to_title_case(name).lower()

	@classmethod
	def get_available_conventions(cls) -> Dict[str, str]:
		"""Get a dictionary of available naming conventions and their descriptions."""
		return {name: info['description'] for name, info in cls.NAMING_CONVENTIONS.items()}

	@classmethod
	def get_convention_examples(cls, convention: str) -> Dict[str, list]:
		"""Get examples for a specific naming convention."""
		if convention in cls.NAMING_CONVENTIONS:
			conv_info = cls.NAMING_CONVENTIONS[convention]
			return {
				'valid': conv_info.get('examples', []),
				'invalid': conv_info.get('invalid_examples', [])
			}
		return {'valid': [], 'invalid': []}

	def validate_config(self) -> list:
		"""Validate the rule configuration and return any warnings."""
		warnings = []

		if self.custom_pattern and self.convention:
			warnings.append("Both 'custom_pattern' and 'convention' specified. Using custom_pattern.")

		if self.min_length < 1:
			warnings.append("min_length should be at least 1")

		if self.max_length and self.max_length < self.min_length:
			warnings.append("max_length should be greater than min_length")

		# Test the regex pattern
		try:
			re.compile(self.pattern)
		except re.error as e:
			warnings.append(f"Invalid regex pattern: {e}")

		# Validate abbreviations
		for abbrev in self.allowed_abbreviations:
			if not abbrev.isupper():
				warnings.append(f"Abbreviation '{abbrev}' should be uppercase")
			if len(abbrev) < 2:
				warnings.append(f"Abbreviation '{abbrev}' should be at least 2 characters long")

		return warnings

	def get_abbreviation_info(self) -> dict:
		"""Get information about configured abbreviations."""
		return {
			'allowed_abbreviations': sorted(list(self.allowed_abbreviations)),
			'auto_detect_enabled': self.auto_detect_abbreviations,
			'common_abbreviations_count':
				len(self.common_abbreviations) if self.auto_detect_abbreviations else 0,
			'total_abbreviations': len(self.all_abbreviations)
		}


# Example configurations for different teams/projects
EXAMPLE_CONFIGS = {
	"strict_pascal": {
		"convention": "PascalCase",
		"allow_numbers": False,
		"min_length": 3,
		"max_length": 50,
		"forbidden_names": ["Button", "Label", "Panel"],
		"allowed_abbreviations": ["XML", "JSON"],
		"auto_detect_abbreviations": True
	},
	"web_style_with_abbreviations": {
		"convention": "kebab-case",
		"allow_numbers": True,
		"min_length": 2,
		"max_length": 30,
		"allowed_abbreviations": ["API", "HTTP", "URL", "XML", "JSON"],
		"auto_detect_abbreviations": False
	},
	"database_style": {
		"convention": "snake_case",
		"allow_numbers": True,
		"min_length": 2,
		"forbidden_names": ["temp", "tmp", "test"],
		"allowed_abbreviations": ["SQL", "API", "ID", "UUID"],
		"auto_detect_abbreviations": True
	},
	"human_readable_with_acronyms": {
		"convention": "Title Case",
		"allow_numbers": True,
		"min_length": 5,
		"max_length": 40,
		"allowed_abbreviations": ["NASA", "GPS", "AI", "ML"],
		"auto_detect_abbreviations": True
	},
	"custom_regex_with_abbreviations": {
		"custom_pattern": r"^(btn|lbl|pnl)[A-Z][a-zA-Z0-9]*$",
		"min_length": 4,
		"max_length": 25,
		"allowed_abbreviations": ["XML", "HTTP", "API"],
		"auto_detect_abbreviations": False
	},
	"tech_company_style": {
		"convention": "PascalCase",
		"allow_numbers": True,
		"min_length": 3,
		"max_length": 40,
		"forbidden_names": ["Component", "Widget", "Element"],
		"allowed_abbreviations": ["AI", "ML", "API", "SDK", "CLI", "GUI", "REST", "GraphQL"],
		"auto_detect_abbreviations": True
	}
}
