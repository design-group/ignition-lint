from .base import LintingRule, Visitor
from .script_rules import ScriptLintingRule, PylintScriptRule
from .binding_rules import BindingRule, PollingIntervalRule

# Map rule names to their classes for configuration
RULES_MAP = {
	"PylintScriptRule": PylintScriptRule,
	"PollingIntervalRule": PollingIntervalRule,
	"ScriptLintingRule": ScriptLintingRule,
	"BindingRule": BindingRule,
}

__all__ = [
	"LintingRule",
	"Visitor",
	"ScriptLintingRule",
	"PylintScriptRule",
	"BindingRule",
	"PollingIntervalRule",
	"RULES_MAP",
]
