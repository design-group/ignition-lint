#!/usr/bin/env python3
"""
Debug script for UnusedCustomPropertiesRule
"""

import sys
import json
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the rule module and extract class manually to avoid registration issues
import ignition_lint.rules.unused_custom_properties as unused_props_module
import inspect

def get_rule_class():
    # Import the rule class directly to avoid registration issues
    from ignition_lint.rules.unused_custom_properties import UnusedCustomPropertiesRule
    return UnusedCustomPropertiesRule
from ignition_lint.common.flatten_json import flatten_json
from ignition_lint.model.builder import ViewModelBuilder


def test_rule_directly():
    """Test the rule directly with minimal data."""
    print("=== Testing UnusedCustomPropertiesRule directly ===")
    
    # Create mixed test data - both used and unused properties
    view_data = {
        "custom": {
            "usedProp": "used",
            "unusedProp": "unused"
        },
        "root": {
            "children": [{
                "meta": {"name": "TestLabel"},
                "type": "ia.display.label", 
                "custom": {
                    "usedComponentProp": "used in binding",
                    "unusedComponentProp": "never used"
                },
                "props": {
                    "text": {
                        "binding": {
                            "type": "expression",
                            "config": {
                                "expression": "{view.custom.usedProp} + {this.custom.usedComponentProp}"
                            }
                        }
                    }
                }
            }],
            "meta": {"name": "root"}
        }
    }
    
    print("1. Original view data:")
    print(json.dumps(view_data, indent=2))
    
    # Flatten the JSON
    flattened = flatten_json(view_data)
    print("\n2. Flattened JSON:")
    for k, v in sorted(flattened.items()):
        print(f"   {k}: {v}")
    
    # Build the model
    builder = ViewModelBuilder()
    model = builder.build_model(flattened)
    print("\n3. Model summary:")
    for node_type, nodes in model.items():
        if nodes:
            print(f"   {node_type}: {len(nodes)} nodes")
            if node_type in ['bindings', 'expression_bindings', 'properties']:
                for node in nodes:
                    print(f"      {node.path}: {getattr(node, 'expression', getattr(node, 'value', 'N/A'))}")
    
    # Test the rule
    UnusedCustomPropertiesRule = get_rule_class()
    if not UnusedCustomPropertiesRule:
        print("   ERROR: Could not find UnusedCustomPropertiesRule class")
        return
    
    rule = UnusedCustomPropertiesRule()
    rule.reset()
    
    print("\n4. Running rule...")
    try:
        # Call the process_nodes method like the LintEngine would
        all_nodes = []
        for node_list in model.values():
            all_nodes.extend(node_list)
        
        print(f"   Processing {len(all_nodes)} total nodes:")
        for node in all_nodes:
            print(f"     - {node.node_type.value}: {node.path}")
            if hasattr(node, 'expression'):
                print(f"       Expression: {node.expression}")
        
        rule.process_nodes(all_nodes)
        
        print(f"   Defined properties: {rule.defined_properties}")
        print(f"   Used properties: {rule.used_properties}")
        print(f"   Errors: {rule.errors}")
        
        if rule.errors:
            print("\n✅ Rule found issues:")
            for error in rule.errors:
                print(f"   - {error}")
        else:
            print("\n❌ Rule found no issues")
            
    except Exception as e:
        print(f"   Error running rule: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_rule_directly()