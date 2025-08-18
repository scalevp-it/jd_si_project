#!/usr/bin/env python3
"""
Simple authentication test for SI API
"""

import sys
import os
import json

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.si_session import SISession

def test_auth():
    """Test basic authentication with SI API"""
    
    print("🔐 Testing SI API Authentication")
    print("=" * 40)
    
    try:
        # Check environment variables
        print("\n1. Checking environment variables:")
        SISession.check_env_vars()
        
        # Create session
        print("\n2. Creating SI session:")
        session = SISession.from_env()
        print(f"   ✅ Session created successfully")
        print(f"   📋 Workspace ID: {session.workspace_id}")
        
        # Test basic API call - get change sets
        print("\n3. Testing basic API call (get change sets):")
        change_sets = session.get_change_sets()
        
        if change_sets:
            print(f"   ✅ API call successful - found {len(change_sets)} change sets:")
            for i, cs in enumerate(change_sets[:3], 1):  # Show first 3
                status = cs.get('status', 'unknown')
                name = cs.get('name', 'unnamed')
                print(f"      {i}. {name} ({status})")
            if len(change_sets) > 3:
                print(f"      ... and {len(change_sets) - 3} more")
        else:
            print("   ❌ API call succeeded but returned no change sets")
            
        # Test schemas API call
        print("\n4. Testing schemas API call (first page only):")
        from system_initiative_api_client import SchemasApi
        
        schemas_api = SchemasApi(session.api_client)
        
        # Simple first page test
        try:
            response = schemas_api.list_schemas_without_preload_content(
                workspace_id=session.workspace_id,
                change_set_id="HEAD",
                limit="50"
            )
            
            if hasattr(response, 'data'):
                raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
                data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                
                if isinstance(data, dict) and 'schemas' in data:
                    schemas = data['schemas']
                    print(f"   ✅ Schemas API call successful - found {len(schemas)} schemas on first page")
                    
                    if schemas:
                        print("   📋 Sample schemas:")
                        for i, schema in enumerate(schemas[:3], 1):
                            name = schema.get('schemaName', schema.get('name', 'unnamed'))
                            installed = schema.get('installed', 'unknown')
                            print(f"      {i}. {name} (installed: {installed})")
                    
                    # Check for pagination info
                    next_cursor = data.get('nextCursor')
                    if next_cursor:
                        print(f"   📄 Pagination available - next cursor: {next_cursor[:20]}...")
                    else:
                        print(f"   📄 No more pages available")
                        
                else:
                    print(f"   ❌ Unexpected response format: {type(data)}")
                    print(f"   Raw response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            else:
                print(f"   ❌ No data in response")
                
        except Exception as schema_error:
            print(f"   ❌ Schemas API call failed: {schema_error}")
        
        print(f"\n✅ Authentication test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_auth()
    exit(0 if success else 1)