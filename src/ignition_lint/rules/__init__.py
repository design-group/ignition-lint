from .base import LintingRule, Visitor
from .script_rules import ScriptLintingRule, PylintScriptRule
from .binding_rules import BindingLintingRule, PollingIntervalRule

# Map rule names to their classes for configuration
RULES_MAP = {
	"PylintScriptRule": PylintScriptRule,
	"PollingIntervalRule": PollingIntervalRule,
	"ScriptLintingRule": ScriptLintingRule,
	"BindingLintingRule": BindingLintingRule,
}

__all__ = [
	"LintingRule",
	"Visitor",
	"ScriptLintingRule",
	"PylintScriptRule",
	"BindingLintingRule",
	"PollingIntervalRule",
	"RULES_MAP",
]
