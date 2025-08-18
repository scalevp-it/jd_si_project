#!/usr/bin/env python3
"""
Get ALL schemas using pagination to find system-wide schemas
"""

import sys
import os
import json

# Add parent directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.si_session import SISession
from system_initiative_api_client import SchemasApi


def get_all_schemas_paginated(change_set_id: str = "HEAD"):
    """
    Get ALL schemas using pagination
    
    Args:
        change_set_id: Change set ID (defaults to "HEAD")
    """
    try:
        session = SISession.from_env()
        schemas_api = SchemasApi(session.api_client)
        
        print(f"🔍 Getting ALL schemas using pagination")
        print(f"📋 Workspace: {session.workspace_id}")
        print(f"🔄 Change set: {change_set_id}")
        print("-" * 60)
        
        all_schemas = []
        cursor = None
        page = 1
        limit = "300"  # Maximum allowed per page
        
        while True:
            print(f"📄 Getting page {page} (limit: {limit}, cursor: {cursor or 'None'})")
            
            # Prepare parameters
            params = {
                'workspace_id': session.workspace_id,
                'change_set_id': change_set_id,
                'limit': limit
            }
            
            if cursor:
                params['cursor'] = cursor
            
            # Get schemas page
            response = schemas_api.list_schemas_without_preload_content(**params)
            
            if not hasattr(response, 'data'):
                print("❌ No data in response")
                break
            
            raw_data = response.data.decode('utf-8') if hasattr(response.data, 'decode') else response.data
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            
            if not isinstance(data, dict):
                print(f"❌ Unexpected response format: {type(data)}")
                break
            
            # Extract schemas from this page
            page_schemas = data.get('schemas', [])
            all_schemas.extend(page_schemas)
            
            print(f"   ✅ Found {len(page_schemas)} schemas on page {page}")
            print(f"   📊 Total schemas so far: {len(all_schemas)}")
            
            # Check for next page
            next_cursor = data.get('nextCursor')
            if not next_cursor:
                print(f"   🏁 No more pages - reached end")
                break
            
            cursor = next_cursor
            page += 1
            
            # Safety check to prevent infinite loops
            if page > 20:
                print(f"   ⚠️ Stopped at page {page} for safety")
                break
        
        print(f"\n📊 TOTAL SCHEMAS FOUND: {len(all_schemas)}")
        
        # Now search through ALL schemas
        print(f"\n🔍 Searching through all {len(all_schemas)} schemas...")
        
        # Look for RDS and other database schemas
        rds_schemas = []
        db_schemas = []
        all_schema_names = []
        
        for i, schema in enumerate(all_schemas):
            # Get schema name
            schema_names = [
                schema.get('schemaName'),
                schema.get('name'),
                schema.get('displayName'),
                schema.get('title')
            ]
            
            primary_name = next((name for name in schema_names if name), f'Unknown-{i}')
            all_schema_names.append(primary_name)
            
            # Check for RDS/database schemas
            name_lower = primary_name.lower()
            if 'rds' in name_lower:
                rds_schemas.append((i+1, primary_name, schema))
            elif 'db' in name_lower or 'database' in name_lower:
                db_schemas.append((i+1, primary_name, schema))
        
        # Show results
        if rds_schemas:
            print(f"\n🎯 FOUND RDS SCHEMAS ({len(rds_schemas)}):")
            for idx, name, schema in rds_schemas:
                print(f"   {idx:3d}. {name}")
                schema_id = schema.get('schemaId', 'N/A')
                print(f"        ID: {schema_id}")
        
        if db_schemas:
            print(f"\n🎯 FOUND DATABASE SCHEMAS ({len(db_schemas)}):")
            for idx, name, schema in db_schemas:
                print(f"   {idx:3d}. {name}")
                schema_id = schema.get('schemaId', 'N/A')
                print(f"        ID: {schema_id}")
        
        if not rds_schemas and not db_schemas:
            print(f"\n❌ No RDS or database schemas found in {len(all_schemas)} schemas")
        
        # Save all schema names to file
        with open('all_schemas_complete.json', 'w') as f:
            json.dump(sorted(all_schema_names), f, indent=2)
        print(f"\n💾 Complete schema list saved to: all_schemas_complete.json")
        
        # Show some interesting schemas
        print(f"\n📋 Sample of all {len(all_schemas)} schemas:")
        for i, name in enumerate(sorted(all_schema_names)):
            if i < 100:  # Show first 100
                print(f"   {i+1:3d}. {name}")
            elif i == 100:
                print(f"   ... and {len(all_schema_names) - 100} more schemas")
                break
        
        # Look for the specific schema we want
        target = "AWS::RDS::DBInstance"
        print(f"\n🎯 Looking specifically for '{target}':")
        found = False
        for i, name in enumerate(all_schema_names):
            if target.lower() == name.lower():
                print(f"   ✅ FOUND: {name} (position {i+1})")
                found = True
                break
            elif target.lower() in name.lower():
                print(f"   🔍 Partial match: {name} (position {i+1})")
        
        if not found:
            print(f"   ❌ '{target}' not found in {len(all_schemas)} schemas")
            # Show closest matches
            matches = [name for name in all_schema_names if 'rds' in name.lower() or 'db' in name.lower()]
            if matches:
                print(f"   💡 Database-related schemas found: {matches}")
        
        return all_schemas
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return []


if __name__ == "__main__":
    print("🚀 Complete Schema Discovery with Pagination")
    print("=" * 60)
    
    schemas = get_all_schemas_paginated()
    
    if schemas:
        print(f"\n✅ Successfully retrieved {len(schemas)} total schemas!")
    else:
        print(f"\n❌ Failed to retrieve schemas!")