#!/usr/bin/env python3
"""
Explore all available methods in the SchemasApi to find system-wide schema listing
"""

import sys
import os
import json

# Add parent directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.si_session import SISession
from system_initiative_api_client import SchemasApi


def explore_schemas_api():
    """Explore all available methods in the SchemasApi"""
    try:
        session = SISession.from_env()
        schemas_api = SchemasApi(session.api_client)
        
        print(f"🔍 Exploring SchemasApi Methods")
        print(f"📋 Workspace: {session.workspace_id}")
        print("=" * 60)
        
        # Get all methods available in the SchemasApi
        all_methods = [method for method in dir(schemas_api) if not method.startswith('_')]
        
        print(f"📊 Found {len(all_methods)} available methods in SchemasApi:")
        print()
        
        # Categorize methods
        list_methods = []
        get_methods = []
        other_methods = []
        
        for method in all_methods:
            if 'list' in method.lower():
                list_methods.append(method)
            elif 'get' in method.lower():
                get_methods.append(method)
            else:
                other_methods.append(method)
        
        # Show list methods (most likely to have system-wide schemas)
        print(f"🔍 LIST Methods ({len(list_methods)}):")
        for i, method in enumerate(list_methods, 1):
            print(f"   {i:2d}. {method}")
        
        print(f"\n🔍 GET Methods ({len(get_methods)}):")
        for i, method in enumerate(get_methods, 1):
            print(f"   {i:2d}. {method}")
        
        print(f"\n🔍 OTHER Methods ({len(other_methods)}):")
        for i, method in enumerate(other_methods, 1):
            print(f"   {i:2d}. {method}")
        
        # Try to get method signatures/help
        print(f"\n" + "="*60)
        print(f"🔍 Method Signatures for List Methods:")
        print("="*60)
        
        for method in list_methods:
            try:
                method_obj = getattr(schemas_api, method)
                if hasattr(method_obj, '__doc__') and method_obj.__doc__:
                    print(f"\n📋 {method}:")
                    print(f"   Doc: {method_obj.__doc__}")
                
                # Try to get signature info
                if hasattr(method_obj, '__annotations__'):
                    print(f"   Annotations: {method_obj.__annotations__}")
                    
            except Exception as e:
                print(f"   ❌ Could not inspect {method}: {e}")
        
        # Test some promising methods
        print(f"\n" + "="*60)
        print(f"🧪 Testing Promising Methods:")
        print("="*60)
        
        # Test methods that might return system-wide schemas
        test_methods = [
            ('list_schemas', {'workspace_id': session.workspace_id, 'change_set_id': 'HEAD'}),
            ('list_schemas_without_preload_content', {'workspace_id': session.workspace_id, 'change_set_id': 'HEAD'}),
        ]
        
        # Try without workspace/changeset params if method exists
        if hasattr(schemas_api, 'list_all_schemas'):
            test_methods.append(('list_all_schemas', {}))
        
        if hasattr(schemas_api, 'list_system_schemas'):
            test_methods.append(('list_system_schemas', {}))
            
        if hasattr(schemas_api, 'get_available_schemas'):
            test_methods.append(('get_available_schemas', {}))
        
        for method_name, params in test_methods:
            if hasattr(schemas_api, method_name):
                print(f"\n🧪 Testing {method_name} with params: {params}")
                try:
                    method = getattr(schemas_api, method_name)
                    
                    if params:
                        if method_name.endswith('_without_preload_content'):
                            result = method(**params)
                            if hasattr(result, 'data'):
                                raw_data = result.data.decode('utf-8') if hasattr(result.data, 'decode') else result.data
                                data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                                print(f"   ✅ Success! Response type: {type(data)}")
                                if isinstance(data, dict):
                                    print(f"   Keys: {list(data.keys())}")
                                    if 'schemas' in data:
                                        print(f"   Found {len(data['schemas'])} schemas")
                                elif isinstance(data, list):
                                    print(f"   Found {len(data)} items")
                        else:
                            result = method(**params)
                            print(f"   ✅ Success! Response type: {type(result)}")
                    else:
                        # Try without any parameters - might return system schemas
                        result = method()
                        print(f"   ✅ Success! Response type: {type(result)}")
                        
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
        
        # Look for any method that might not require workspace_id
        print(f"\n🔍 Looking for methods that might work without workspace_id...")
        for method in all_methods:
            if 'schema' in method.lower() and method not in ['list_schemas', 'list_schemas_without_preload_content']:
                print(f"   Found: {method}")
                try:
                    method_obj = getattr(schemas_api, method)
                    print(f"      Trying {method} without parameters...")
                    # This is risky but let's see what happens
                    if method.startswith('list') or method.startswith('get'):
                        result = method_obj()
                        print(f"      ✅ {method}() worked! Type: {type(result)}")
                except Exception as e:
                    print(f"      ❌ {method}() failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("🚀 SchemasApi Method Explorer")
    print("=" * 50)
    
    success = explore_schemas_api()
    
    if success:
        print(f"\n✅ API exploration completed!")
    else:
        print(f"\n❌ API exploration failed!")