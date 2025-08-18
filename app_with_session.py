"""
Main application for System Initiative API interactions using SISession
"""

import sys
import os

# Add current directory to Python path to find src module
sys.path.insert(0, os.path.dirname(__file__))

from src.si_session import SISession, SISessionManager
from src.component_helpers import (
    add_component,
    list_available_schemas,
    get_component_by_name,
    list_components,
    test_imports
)


def main():
    """Main application entry point"""
    
    print("System Initiative API Client with Session Management")
    print("=" * 55)
    
    # First, test that all imports are working
    print("\n0. Testing imports:")
    if not test_imports():
        print("✗ Import test failed. Please check your installation.")
        return 1
    
    # Configuration - Update these values for your environment
    SI_HOST = "http://localhost"              # Your SI server URL
    API_TOKEN = None                          # Your API token (if required)
    WORKSPACE_ID = "your-workspace-id"        # Your actual workspace ID
    
    try:
        # Create SI session
        print(f"\n1. Creating System Initiative session:")
        session = SISession(
            si_host=SI_HOST,
            workspace_id=WORKSPACE_ID,
            api_token=API_TOKEN,
            verify_ssl=True  # Set to False for local development if needed
        )
        
        print(f"✓ Session created: {session}")
        
        # Test connection (optional - comment out if whoami endpoint doesn't exist)
        # print(f"\n2. Testing connection:")
        # session.test_connection()
        
        # Get available change sets
        print(f"\n2. Getting available change sets:")
        change_sets = session.get_change_sets()
        
        if not change_sets:
            print("No change sets found. Creating a new one...")
            change_set_id = session.create_change_set("api-test-changeset")
            if not change_set_id:
                print("✗ Failed to create change set. Exiting.")
                return 1
        else:
            # Use the first available change set
            change_set_id = change_sets[0]["id"]
            print(f"Using change set: {change_sets[0]['name']} (ID: {change_set_id})")
        
        # List available schemas
        print(f"\n3. Listing available schemas:")
        schemas = list_available_schemas(
            session.api_client,  # Pass the api_client directly for now
            session.workspace_id,
            change_set_id
        )
        
        # List existing components
        print(f"\n4. Listing existing components:")
        components = list_components(
            session.api_client,
            session.workspace_id,
            change_set_id
        )
        
        # Example: Create a new component (uncomment to use)
        # print(f"\n5. Creating a new component:")
        # if schemas:
        #     schema_name = schemas[0]["name"]
        #     try:
        #         component_id = add_component(
        #             session,  # Pass the session directly
        #             change_set_id=change_set_id,
        #             schema_name=schema_name,
        #             component_name=f"api-test-{int(time.time())}",
        #             attributes={
        #                 "description": "Test component created via API session"
        #             }
        #         )
        #         print(f"✓ Component created with ID: {component_id}")
        #     except Exception as e:
        #         print(f"✗ Failed to create component: {e}")
        
        print(f"\n✓ Application completed successfully!")
        print(f"Session info: {session}")
        
    except Exception as e:
        print(f"\n✗ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def session_manager_example():
    """Example of using the session manager for multiple environments"""
    
    print("\nSession Manager Example")
    print("=" * 30)
    
    # Create session manager
    manager = SISessionManager()
    
    # Add different environments
    dev_session = manager.add_session(
        name="development",
        si_host="http://localhost:3000",
        workspace_id="dev-workspace-id",
        api_token=None,
        set_as_default=True
    )
    
    staging_session = manager.add_session(
        name="staging", 
        si_host="https://staging.systeminit.com",
        workspace_id="staging-workspace-id",
        api_token="staging-token-here"
    )
    
    prod_session = manager.add_session(
        name="production",
        si_host="https://app.systeminit.com", 
        workspace_id="prod-workspace-id",
        api_token="prod-token-here"
    )
    
    # List all sessions
    manager.list_sessions()
    
    # Use different sessions
    print(f"\nUsing development session:")
    dev = manager.get_session("development")
    print(f"Development: {dev}")
    
    print(f"\nUsing default session:")
    default = manager.get_session()  # Gets default
    print(f"Default: {default}")


if __name__ == "__main__":
    # Run main application
    result = main()
    
    # Uncomment to see session manager example
    # session_manager_example()
    
    exit(result)