#!/usr/bin/env python3
"""
Debug script to validate Property node creation in the model builder.
Tests different JSON structures to understand what gets created as Property nodes.
"""

import sys
import json
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ignition_lint.common.flatten_json import flatten_json
from ignition_lint.model.builder import ViewModelBuilder


def test_property_node_creation():
    """Test different JSON structures to see what Property nodes get created."""
    
    # Test Case 1: View-level custom properties and params
    print("=" * 60)
    print("TEST CASE 1: View-level properties")
    print("=" * 60)
    
    view_data_1 = {
        "custom": {"viewCustomProp": "custom value"},
        "params": {"viewParam": "param value"},
        "props": {"viewProp": "prop value"},
        "root": {
            "meta": {"name": "root"}
        }
    }
    
    analyze_view_data("View-level properties", view_data_1)
    
    # Test Case 2: Component-level custom properties
    print("\n" + "=" * 60)
    print("TEST CASE 2: Component-level properties")
    print("=" * 60)
    
    view_data_2 = {
        "root": {
            "children": [{
                "meta": {"name": "TestButton"},
                "type": "ia.input.button",
                "custom": {"componentCustomProp": "custom value"},
                "props": {"text": "Button Text"}
            }],
            "meta": {"name": "root"}
        }
    }
    
    analyze_view_data("Component-level properties", view_data_2)
    
    # Test Case 3: Binding expressions
    print("\n" + "=" * 60)
    print("TEST CASE 3: Binding expressions")
    print("=" * 60)
    
    view_data_3 = {
        "root": {
            "children": [{
                "meta": {"name": "TestLabel"},
                "type": "ia.display.label",
                "props": {
                    "text": {
                        "binding": {
                            "type": "expression",
                            "config": {
                                "expression": "{view.custom.someProp}"
                            }
                        }
                    }
                }
            }],
            "meta": {"name": "root"}
        }
    }
    
    analyze_view_data("Binding expressions", view_data_3)
    
    # Test Case 4: Real-world complex example - PascalCase
    print("\n" + "=" * 60)
    print("TEST CASE 4: PascalCase test (simple)")
    print("=" * 60)
    
    try:
        from ignition_lint.common.flatten_json import read_json_file
        real_data = read_json_file('./tests/cases/PascalCase/view.json')
        analyze_view_data("PascalCase test file", real_data)
    except Exception as e:
        print(f"Could not load PascalCase test file: {e}")
    
    # Test Case 5: LineDashboard - Complex binding-created properties
    print("\n" + "=" * 60)
    print("TEST CASE 5: LineDashboard (persistent vs non-persistent)")
    print("=" * 60)
    
    try:
        line_data = read_json_file('./tests/cases/LineDashboard/view.json')
        analyze_line_dashboard_properties(line_data)
    except Exception as e:
        print(f"Could not load LineDashboard test file: {e}")


def analyze_line_dashboard_properties(view_data):
    """Analyze LineDashboard to understand persistent vs non-persistent properties."""
    print(f"\n📋 LineDashboard - Persistent vs Non-Persistent Analysis")
    print("-" * 60)
    
    # Flatten the JSON
    flattened = flatten_json(view_data)
    
    # Find all custom and params properties
    custom_props = {}
    param_props = {}
    prop_config_props = {}
    
    for path, value in flattened.items():
        if '.custom.' in path and not path.startswith('propConfig.'):
            custom_props[path] = value
        elif path.startswith('params.'):
            param_props[path] = value
        elif path.startswith('propConfig.custom.'):
            prop_config_props[path] = value
    
    print(f"🔍 Found Properties:")
    print(f"  Custom properties: {len(custom_props)}")
    print(f"  View parameters: {len(param_props)}")  
    print(f"  PropConfig custom: {len(prop_config_props)}")
    
    # Analyze propConfig properties for persistence
    print(f"\n📊 PropConfig Custom Properties (with persistence info):")
    persistent_props = []
    non_persistent_props = []
    
    for path, value in prop_config_props.items():
        if path.endswith('.persistent'):
            prop_path = path.replace('.persistent', '')
            is_persistent = value
            if is_persistent:
                persistent_props.append(prop_path)
            else:
                non_persistent_props.append(prop_path)
            print(f"  {prop_path}: persistent={is_persistent}")
    
    print(f"\n✅ Persistent Properties ({len(persistent_props)}):")
    for prop in persistent_props:
        # Find corresponding actual property
        actual_path = prop.replace('propConfig.', '')
        actual_value = flattened.get(actual_path, "NOT FOUND")
        print(f"  {prop} → {actual_path}: {actual_value}")
    
    print(f"\n⏳ Non-Persistent Properties ({len(non_persistent_props)}):")
    for prop in non_persistent_props:
        # Check if actual property exists (should not for non-persistent)
        actual_path = prop.replace('propConfig.', '')
        actual_value = flattened.get(actual_path, "NOT FOUND")
        has_binding = any(f"{actual_path}.binding" in p for p in flattened.keys())
        print(f"  {prop} → {actual_path}: {actual_value} (binding: {has_binding})")
    
    # Analyze regular custom properties
    print(f"\n🏷️  Regular Custom Properties ({len(custom_props)}):")
    for path, value in custom_props.items():
        # Check if this has propConfig
        config_path = f"propConfig.{path}"
        has_config = any(p.startswith(config_path) for p in flattened.keys())
        persistent_path = f"{config_path}.persistent"
        is_persistent = flattened.get(persistent_path, True)  # Default to persistent
        print(f"  {path}: {value} (configured: {has_config}, persistent: {is_persistent})")
    
    # Build model and see what becomes Property nodes
    builder = ViewModelBuilder()
    model = builder.build_model(flattened)
    properties = model.get('properties', [])
    
    print(f"\n🏗️  Current Model Builder Results:")
    print(f"  Property nodes created: {len(properties)}")
    for prop in properties:
        if '.custom.' in prop.path or prop.path.startswith('params.'):
            # Check if this should be persistent
            config_path = f"propConfig.{prop.path}"
            persistent_path = f"{config_path}.persistent"
            is_persistent = flattened.get(persistent_path, True)
            print(f"    {prop.path}: {prop.value} (persistent: {is_persistent})")


def analyze_view_data(test_name, view_data):
    """Analyze a specific view data structure."""
    print(f"\n📋 {test_name}")
    print("-" * 40)
    
    # Show original structure (abbreviated)
    print("Original JSON structure:")
    print(json.dumps(view_data, indent=2)[:500] + ("..." if len(json.dumps(view_data)) > 500 else ""))
    
    # Flatten the JSON
    flattened = flatten_json(view_data)
    print(f"\n📊 Flattened JSON ({len(flattened)} items):")
    for path, value in sorted(flattened.items()):
        print(f"  {path}: {value}")
    
    # Build the model
    builder = ViewModelBuilder()
    model = builder.build_model(flattened)
    
    print(f"\n🏗️  Model Summary:")
    total_nodes = 0
    for node_type, nodes in model.items():
        if nodes:
            print(f"  {node_type}: {len(nodes)} nodes")
            total_nodes += len(nodes)
        
    print(f"  TOTAL: {total_nodes} nodes")
    
    # Show Property nodes in detail
    properties = model.get('properties', [])
    if properties:
        print(f"\n🔍 Property Nodes Detail ({len(properties)} nodes):")
        for prop in properties:
            print(f"  Path: {prop.path}")
            print(f"    Name: {prop.name}")
            print(f"    Value: {prop.value}")
            print(f"    Type: {type(prop.value)}")
            print()
    else:
        print("\n❌ NO Property nodes created")
    
    # Analyze what's NOT becoming Property nodes
    print("\n🚫 Paths NOT converted to Property nodes:")
    component_paths = [comp.path for comp in model.get('components', [])]
    
    for path, value in sorted(flattened.items()):
        # Check if this path became a Property node
        became_property = any(prop.path == path for prop in properties)
        
        if not became_property:
            print(f"  {path}: {value}")
            
            # Try to understand WHY it didn't become a property
            reasons = []
            if any(f".{skip}." in path for skip in ['meta', 'binding', 'scripts', 'events']):
                matching_skips = [skip for skip in ['meta', 'binding', 'scripts', 'events'] if f".{skip}." in path]
                reasons.append(f"contains skipped section: {matching_skips}")
            if path.endswith('.type'):
                reasons.append("ends with .type")
            if not any(path.startswith(comp_path) for comp_path in component_paths):
                reasons.append("doesn't belong to any component")
                
            if reasons:
                print(f"    Reason: {', '.join(reasons)}")
            else:
                print(f"    Reason: UNKNOWN - should be investigated!")


if __name__ == "__main__":
    test_property_node_creation()