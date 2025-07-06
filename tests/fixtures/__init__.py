# tests/fixtures/__init__.py
"""
Test fixtures and utilities for ignition-lint tests.
"""

from .base_test import BaseRuleTest, BaseIntegrationTest
from .test_helpers import (create_mock_view, assert_rule_errors, assert_no_errors, get_test_config)
from .config_framework import ConfigurableTestFramework, create_sample_test_configs

__all__ = [
	'BaseRuleTest', 'BaseIntegrationTest', 'create_mock_view', 'assert_rule_errors', 'assert_no_errors',
	'get_test_config', 'ConfigurableTestFramework', 'create_sample_test_configs'
]
