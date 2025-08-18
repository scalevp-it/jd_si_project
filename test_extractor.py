#!/usr/bin/env python3
"""
Test the changeset component extractor
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.changeset_extractor import extract_changeset_components

def test_extractor():
    """Test the changeset component extractor"""
    
    print("🧪 Testing Changeset Component Extractor")
    print("=" * 45)
    
    # Use HEAD changeset for testing
    change_set_id = "HEAD"
    
    try:
        print(f"\n🚀 Testing extraction from changeset: {change_set_id}")
        
        # First, let's see what the components look like
        from src.si_session import SISession
        session = SISession.from_env()
        components = session.get_components(change_set_id)
        
        if components:
            print(f"\n🔍 Sample component structure:")
            print(f"   Keys: {list(components[0].keys())}")
            print(f"   First component: {components[0]}")
        
        result = extract_changeset_components(change_set_id, quiet=False)
        
        if result["success"]:
            print(f"\n✅ Extractor test completed successfully!")
            print(f"   Components found: {result['component_count']}")
            print(f"   Successfully extracted: {result['successful_extractions']}")
            if result.get('failed_extractions', 0) > 0:
                print(f"   Failed extractions: {result['failed_extractions']}")
            print(f"   Output directory: {result.get('output_directory', 'unknown')}")
        else:
            print(f"\n❌ Extractor test failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
        return result["success"]
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extractor()
    exit(0 if success else 1)