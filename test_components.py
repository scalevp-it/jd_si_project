#!/usr/bin/env python3
"""
Test script for component listing functionality
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.si_session import SISession


def test_component_listing():
    """Test the component listing functionality"""
    
    print("🧪 Testing Component Listing")
    print("=" * 35)
    
    try:
        # Test 1: Check environment variables
        print("\n1. Environment Variables Check:")
        SISession.check_env_vars()
        
        # Test 2: Create session
        print("\n2. Creating Session:")
        session = SISession.from_env()
        
        # Test 3: Test API connection (if whoami endpoint exists)
        print("\n3. Testing Connection:")
        try:
            connection_ok = session.test_connection()
            if not connection_ok:
                print("⚠️  Connection test failed, but continuing...")
        except Exception as e:
            print(f"⚠️  Connection test not available: {e}")
        
        # Test 4: Get change sets
        print("\n4. Getting Change Sets:")
        change_sets = session.get_change_sets()
        
        if not change_sets:
            print("❌ No change sets found. Cannot proceed with component listing.")
            return False
        
        change_set_id = change_sets[0]["id"]
        print(f"✅ Using change set: {change_sets[0]['name']}")
        
        # Test 5: List components
        print("\n5. Listing Components:")
        from src.component_helpers import list_components
        
        components = list_components(
            session,  # Pass session directly 
            session.workspace_id,
            change_set_id,
            limit=10
        )
        
        print(f"✅ Successfully retrieved {len(components)} components")
        
        # Test 6: List schemas
        print("\n6. Listing Available Schemas:")
        from src.component_helpers import list_available_schemas
        
        schemas = list_available_schemas(
            session,
            session.workspace_id, 
            change_set_id,
            limit=5
        )
        
        print(f"✅ Successfully retrieved {len(schemas)} schemas")
        
        print(f"\n🎉 All tests passed!")
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("💡 Make sure to set your environment variables:")
        print("   export SI_WORKSPACE_ID='your-workspace-id'")
        print("   export SI_API_TOKEN='your-token'  # if needed")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def quick_test():
    """Quick test of just the imports and session creation"""
    
    print("⚡ Quick Test")
    print("=" * 15)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.si_session import SISession
        from src.component_helpers import list_components, list_available_schemas
        print("✅ Imports successful")
        
        # Test session creation
        print("2. Testing session creation...")
        SISession.check_env_vars()
        
        session = SISession.from_env()
        print(f"✅ Session created: {session}")
        
        print("\n🎉 Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = quick_test()
    else:
        success = test_component_listing()
    
    if not success:
        print(f"\n💡 Troubleshooting tips:")
        print(f"  - Run with --quick flag to test just imports")
        print(f"  - Make sure you have SI_WORKSPACE_ID set")
        print(f"  - Check that your SI server is accessible")
        print(f"  - Verify you have at least one change set in your workspace")
        
    exit(0 if success else 1)