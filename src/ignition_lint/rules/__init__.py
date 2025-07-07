from .common import LintingRule, NodeVisitor, BindingRule
from .lint_script import PylintScriptRule
from .polling_interval import PollingIntervalRule
from .name_pattern import NamePatternRule

# Map rule names to their classes for configuration
RULES_MAP = {
	"PylintScriptRule": PylintScriptRule,
	"PollingIntervalRule": PollingIntervalRule,
	"BindingRule": BindingRule,
	"NamePatternRule": NamePatternRule,
}

__all__ = [
	"LintingRule",
	"NodeVisitor",
	"PylintScriptRule",
	"BindingRule",
	"PollingIntervalRule",
	"NamePatternRule",
	"RULES_MAP",
]
