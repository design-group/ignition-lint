from .common import LintingRule, NodeVisitor, BindingRule
from .lint_script import PylintScriptRule
from .polling_interval import PollingIntervalRule
from .component_name import ComponentNameRule

# Map rule names to their classes for configuration
RULES_MAP = {
	"PylintScriptRule": PylintScriptRule,
	"PollingIntervalRule": PollingIntervalRule,
	"BindingRule": BindingRule,
	"ComponentNameRule": ComponentNameRule,
}

__all__ = [
	"LintingRule",
	"NodeVisitor",
	"PylintScriptRule",
	"BindingRule",
	"PollingIntervalRule",
	"RULES_MAP",
]
